import hashlib
import re
from backend.app.graph.client import DomainError
from backend.app.graph.queries import Q5, Q7
from backend.app.ingest.entities import Catalog
from redis.exceptions import ResponseError


def claim_evidence(g, ident, trace=None, require_active=True):
    rows = g.read(Q5, {"claim_id": ident}, "Q5", trace)
    if not rows:
        raise DomainError("NOT_FOUND", "Unknown claim", 404)
    r = rows[0]
    c = r["claim"]
    field = c["anchor_field"]
    text = (
        r["source_body"]
        if field == "body"
        else r["source_raw_text"]
        if field == "raw_text"
        else ""
    )
    valid = (
        text[c["start"] : c["end"]] == c["excerpt"]
        and hashlib.sha256(r["source_raw_text"].encode()).hexdigest()
        == r["source_sha256"]
    )
    if not valid or (require_active and c["status"] != "verified"):
        raise DomainError(
            "INVALID_EVIDENCE", "Claim anchor is invalid or inactive", 409
        )
    return {**c, "source_sha256": r["source_sha256"], "anchor_verified": valid}


def get_source(g, ident, trace=None):
    rows = g.read(
        "MATCH (s:Source {id:$id}) RETURN properties(s) AS source",
        {"id": ident},
        "SOURCE",
        trace,
    )
    if not rows:
        raise DomainError("NOT_FOUND", "Unknown source", 404)
    src = rows[0]["source"]
    src["claims"] = g.read(
        "MATCH (c:Claim {source_id:$id}) RETURN properties(c) AS claim ORDER BY c.id",
        {"id": ident},
        "SOURCE_CLAIMS",
        trace,
    )
    src["claims"] = [r["claim"] for r in src["claims"]]
    src["revisions"] = g.read(
        "MATCH (r:SourceRevision {source_id:$id}) RETURN r.id AS id,r.sha256 AS sha256,r.created_at AS created_at",
        {"id": ident},
        "SOURCE_HISTORY",
        trace,
    )
    return src


def search(g, alias, kind=None, limit=20, trace=None, internal=False):
    # Native full-text receives plain word tokens, never query operators.
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 _-]{2,79}", alias):
        raise DomainError(
            "INVALID_QUERY", "Use a plain entity alias of 3 to 80 characters"
        )
    limit = max(1, min(limit, 80 if internal else 20))
    if alias.casefold().startswith("svc-"):
        entity = Catalog().by_id.get(alias.casefold())
        if entity:
            alias = entity["name"]
    safe = '"' + " ".join(re.findall(r"[A-Za-z0-9]+", alias)) + '"'
    try:
        rows = g.read(Q7, {"safe_query": safe}, "Q7", trace)
    except ResponseError as error:
        raise DomainError(
            "SEARCH_UNAVAILABLE",
            "Native search rejected this alias; try a plain entity name.",
            503,
        ) from error
    result = []
    pattern = re.compile(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", re.I)
    for row in rows:
        src = get_source(g, row["source_id"], trace)
        m = pattern.search(src["body"])
        if not m or (kind and src["kind"] != kind):
            continue
        mention_id = f"mention:{src['id']}:{src['sha256']}:{m.start()}:{m.end()}"
        begin = src["body"].rfind("\n", 0, m.start()) + 1
        end = src["body"].find("\n", m.end())
        paragraph = src["body"][begin : end if end >= 0 else len(src["body"])]
        result.append(
            {
                **row,
                "excerpt": m[0],
                "context": paragraph[:1000],
                "start": m.start(),
                "end": m.end(),
                "source_sha256": src["sha256"],
                "mention_id": mention_id,
                "exact_match": True,
            }
        )
        if len(result) >= limit:
            break
    return result
