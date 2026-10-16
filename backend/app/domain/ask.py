"""Deterministic company questions backed exclusively by Graph.read/GRAPH.RO_QUERY."""

import hashlib
import re
from difflib import SequenceMatcher
from time import perf_counter

from backend.app.graph import ask_queries as Q
from backend.app.graph.client import LOCK, DomainError

SHAPES = [
    "Who owns <service>?",
    "What depends on <service>?",
    "What would replacing <service> affect?",
    "Which projects use <service>?",
    "Who should review a change to <service>?",
    "What documents mention <service>?",
]
PATTERNS = [
    ("owners", r"who owns (.+)"),
    ("dependents", r"what depends on (.+)"),
    ("dependents", r"what would replacing (.+) affect"),
    ("projects", r"which projects use (.+)"),
    ("reviewers", r"who should review a change to (.+)"),
    ("documents", r"what documents mention (.+)"),
]


def parse_question(question):
    text = " ".join(question.strip().removesuffix("?").split())
    for intent, pattern in PATTERNS:
        match = re.fullmatch(pattern, text, re.I)
        if match:
            entity = match[1].strip().strip('"\'')
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{1,79}", entity):
                return intent, entity
    return None


def normalized(value):
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def resolve_entity(entity, nodes):
    """Fuzzy suggestions over current Service nodes, never a file-backed oracle.

    Only a unique exact name/id/alias is selected automatically. Even a single
    fuzzy result needs confirmation, preventing typo guesses from becoming facts.
    """
    target = normalized(entity)
    exact, suggestions = [], []
    for node in nodes:
        aliases = [node["id"], node["name"], *(node.get("aliases") or [])]
        values = {normalized(a) for a in aliases}
        if target in values:
            exact.append(node)
        score = max(SequenceMatcher(None, target, a).ratio() for a in values)
        if any(target in a.split() or target in a for a in values):
            score = max(score, .85)
        if score >= .62:
            suggestions.append((score, node))
    if len(exact) == 1:
        return exact[0], []
    candidates = exact if exact else [n for _, n in sorted(
        suggestions, key=lambda pair: (-pair[0], pair[1]["name"], pair[1]["id"]))]
    return None, [dict(id=n["id"], name=n["name"]) for n in candidates[:6]]


def verified_citations(g, claim_ids, trace):
    if not claim_ids:
        return []
    result = []
    for row in g.read(Q.CITATIONS, {"claim_ids": sorted(claim_ids)}, "ASK_CITATIONS", trace):
        claim = row["claim"]
        text = row.get("source_" + claim["anchor_field"], "")
        if (claim["status"] != "verified"
                or text[claim["start"]:claim["end"]] != claim["excerpt"]
                or hashlib.sha256(row["source_raw_text"].encode()).hexdigest() != row["source_sha256"]):
            raise DomainError("INVALID_EVIDENCE", "A source anchor could not be verified.", 409)
        result.append(dict(id=claim["id"], source_id=claim["source_id"],
                           anchor_field=claim["anchor_field"], start=claim["start"],
                           end=claim["end"], excerpt=claim["excerpt"],
                           source_sha256=row["source_sha256"], anchor_verified=True))
    if {c["id"] for c in result} != claim_ids:
        raise DomainError("INVALID_EVIDENCE", "A supporting claim is missing.", 409)
    return result


def ownership_status(rows):
    owners = {r["owner_id"] for r in rows if r.get("owner_id")}
    return "gap" if not owners else "conflict" if len(owners) > 1 else "single_primary"


def ask(g, question):
    started = perf_counter()
    trace = []
    result = dict(status="unsupported", question=question, intent=None, service=None,
                  message="This question is not supported. Choose one of the supported shapes below.",
                  supported_shapes=SHAPES, suggestions=[], rows=[], citations=[],
                  counts={}, max_hops=5, truncated=False, truncation_examples=[], cycle_detected=False,
                  row_count=0, graph_revision=0, query_trace=trace, query_ms=0.0,
                  elapsed_ms=0.0, source_mode="live_falkordb")
    parsed = parse_question(question)
    # Unsupported questions do no database work and never call a model.
    if not parsed:
        result["elapsed_ms"] = round((perf_counter() - started) * 1000, 3)
        return result
    intent, entity = parsed
    result["intent"] = intent
    with LOCK:
        def revision():
            rows = g.read(Q.REVISION, {}, "ASK_REVISION", trace)
            return int(rows[0]["revision"]) if rows else 0

        result["graph_revision"] = revision()
        nodes = g.read(Q.ENTITIES, {}, "ASK_ENTITIES", trace)
        service, suggestions = resolve_entity(entity, nodes)
        if not service:
            result.update(status="ambiguous" if suggestions else "not_found", suggestions=suggestions,
                          message="Did you mean…" if suggestions else "No matching service is recorded. Try an exact service name.")
        else:
            result.update(status="answered", service=dict(id=service["id"], name=service["name"]))
            ident, name = service["id"], service["name"]
            by_id = {n["id"]: n for n in nodes}
            claim_ids = set()
            rows = []
            if intent in ("dependents", "reviewers"):
                # Native reverse traversal, same minimum-depth/frontier semantics as preview.
                paths = {ident: ([], 0, [ident])}
                raw_paths = g.read(Q.DEPENDENTS, {"root_id": ident}, "ASK_DEPENDENTS", trace)
                for path in raw_paths:
                    ids = path["service_path"]
                    result["cycle_detected"] |= len(set(ids)) < len(ids)
                    candidate = (path["claim_path"], path["hops"], ids)
                    previous = paths.get(path["service_id"])
                    if previous is None or (candidate[1], candidate[2], candidate[0]) < (previous[1], previous[2], previous[0]):
                        paths[path["service_id"]] = candidate
                affected = sorted(paths)
                boundary = [i for i in affected if paths[i][1] == 5]
                beyond = g.read(Q.FRONTIER, {"boundary": boundary, "ids": affected}, "ASK_FRONTIER", trace)
                result["truncated"] = bool(beyond)
                examples = {r["id"]: r for r in beyond}
                result["truncation_examples"] = [dict(service_id=r["id"], name=r["name"], depth=6)
                                                  for r in sorted(examples.values(), key=lambda r: (r["name"], r["id"]))[:3]]
                projects = g.read(Q.PROJECTS, {"ids": affected}, "ASK_PROJECTS", trace)
                claim_ids.update(p["claim_id"] for p in projects)
                claim_ids.update(r["claim_id"] for r in beyond)
                for claims, _, _ in paths.values():
                    claim_ids.update(claims)
                result["counts"] = dict(services=len(affected), projects=len({p["project_id"] for p in projects}))
                if intent == "dependents":
                    rows = [dict(service_id=i, label=by_id[i]["name"], depth=paths[i][1],
                                 detail="Replacement target (included in scope)" if i == ident else " → ".join(by_id[x]["name"] for x in paths[i][2]),
                                 evidence_ids=paths[i][0]) for i in sorted(affected, key=lambda i: (paths[i][1], i))]
                    result["message"] = f"{len(affected) - 1} downstream services plus {name} itself are in the verified 5-hop scope; {result['counts']['projects']} projects use those services."
                else:
                    raw = g.read(Q.REVIEWERS, {"ids": affected}, "ASK_REVIEWERS", trace)
                    for row in raw:
                        status = ownership_status([r for r in raw if r["service_id"] == row["service_id"]])
                        evidence_ids = [c for c in [row["claim_id"], row["membership_claim_id"], *paths[row["service_id"]][0]] if c]
                        claim_ids.update(evidence_ids)
                        rows.append(dict(**row, label=row["owner"] or "unassigned: needs decision", owner_status=status,
                                         detail=f"{row['service']} · {row['team'] or 'No verified team recorded'} · {status.replace('_', ' ')}",
                                         evidence_ids=evidence_ids))
                    people = {r["owner_id"] for r in raw if r["owner_id"]}
                    teams = {r["team_id"] for r in raw if r["team_id"]}
                    result["counts"].update(reviewers=len(people), teams=len(teams))
                    result["message"] = f"Suggest {len(people)} recorded owners and {len(teams)} connected teams for review across {len(affected)} services. Conflicts and gaps still need a human decision; this assigns no work."
            elif intent == "owners":
                raw = g.read(Q.OWNERS, {"ids": [ident]}, "ASK_OWNERS", trace)
                status = ownership_status(raw)
                result["counts"] = dict(owners=len({r["owner_id"] for r in raw if r["owner_id"]}))
                rows = [dict(**r, label=r["owner"] or "No verified primary owner recorded", owner_status=status,
                             detail=name + " · " + status.replace('_', ' '), evidence_ids=[r["claim_id"]] if r["claim_id"] else []) for r in raw]
                claim_ids.update(r["claim_id"] for r in raw if r["claim_id"])
                result["message"] = (f"Ownership conflict: {name} has {result['counts']['owners']} recorded primary owners. Reconcile both source assertions before assigning work." if status == "conflict" else
                                     f"Ownership gap: no verified primary owner is recorded for {name}. This does not prove that nobody owns it." if status == "gap" else
                                     f"{name} has one recorded primary owner: {raw[0]['owner']}.")
            elif intent == "projects":
                raw = g.read(Q.PROJECTS, {"ids": [ident]}, "ASK_PROJECTS", trace)
                rows = [dict(**r, label=r["project"], detail=f"Directly uses {name}", evidence_ids=[r["claim_id"]]) for r in raw]
                claim_ids.update(r["claim_id"] for r in raw)
                result["message"] = f"{len(rows)} projects have a verified direct USES relationship to {name}."
            else:
                # Tokenize live aliases into quoted FT phrases, never accept FT operators.
                aliases = sorted({name, *(service.get("aliases") or [])})
                phrases = ['"' + " ".join(re.findall(r"[A-Za-z0-9]+", a)) + '"' for a in aliases]
                # FalkorDB's native FT syntax does not treat the word OR as a
                # disjunction. Query each quoted alias and deduplicate sources.
                documents = {}
                for phrase in sorted(set(phrases)):
                    for doc in g.read(Q.DOCUMENTS, {"safe_query": phrase}, "ASK_DOCUMENTS", trace):
                        old = documents.get(doc["source_id"])
                        if old is None or doc["ft_score"] > old["ft_score"]:
                            documents[doc["source_id"]] = doc
                raw = sorted(documents.values(), key=lambda d: (-d["ft_score"], d["source_id"]))
                pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True)) + r")(?!\w)", re.I)
                for doc in raw:
                    match = pattern.search(doc["body"])
                    if not match:
                        continue
                    if hashlib.sha256(doc["raw_text"].encode()).hexdigest() != doc["sha256"]:
                        raise DomainError("INVALID_EVIDENCE", "Document hash does not match its source.", 409)
                    cid = f"mention:{doc['source_id']}:{doc['sha256']}:{match.start()}:{match.end()}"
                    begin = doc["body"].rfind("\n", 0, match.start()) + 1
                    end = doc["body"].find("\n", match.end())
                    context = doc["body"][begin:end if end >= 0 else len(doc["body"])]
                    result["citations"].append(dict(id=cid, source_id=doc["source_id"], anchor_field="body", start=match.start(), end=match.end(),
                                                    excerpt=match[0], context=context, source_sha256=doc["sha256"], anchor_verified=True))
                    rows.append(dict(label=doc["title"], detail=context, source_id=doc["source_id"], ft_score=doc["ft_score"], evidence_ids=[cid]))
                result["message"] = f"{len(rows)} documents match a recorded alias for {name}, with exact body-text spans rechecked after native full-text search (up to 80 candidates per alias)."
            # A verified description anchors the target, including an owner gap or zero-result answer.
            descriptions = g.read(Q.DESCRIPTIONS, {"ids": [ident]}, "ASK_DESCRIPTIONS", trace)
            claim_ids.update(r["claim_id"] for r in descriptions)
            result["citations"].extend(verified_citations(g, claim_ids, trace))
            result.update(rows=rows, row_count=len(rows))
        if revision() != result["graph_revision"]:
            raise DomainError("STALE_ANALYSIS", "Graph changed during the question. Retry for a consistent answer.", 409)
        result["query_ms"] = round(sum(t["elapsed_ms"] for t in trace), 3)
        for entry in trace:
            entry["graph_revision"] = result["graph_revision"]
    result["elapsed_ms"] = round((perf_counter() - started) * 1000, 3)
    return result
