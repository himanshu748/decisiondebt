from datetime import datetime
from time import perf_counter
from backend.app.graph.client import LOCK, DomainError
from backend.app.graph.queries import Q1, Q2, Q3, Q4
from backend.app.domain.drift import classify
from backend.app.domain.rank import rank

DEFAULT_AS_OF = "2026-10-15T12:00:00+05:30"


def ownership(g, service_id, trace=None):
    rows = g.read(Q4, {"service_id": service_id}, "Q4", trace)
    primary = sorted({r["owner_id"] for r in rows if r["role"] == "primary"})
    return {
        "owner_status": "unowned"
        if not primary
        else "single_primary"
        if len(primary) == 1
        else "conflict",
        "owner_ids": primary,
        "ownership_claims": rows,
    }


def preview(g, decision_id, as_of=DEFAULT_AS_OF):
    start = perf_counter()
    trace = []
    try:
        when = datetime.fromisoformat(as_of)
    except ValueError:
        raise DomainError("INVALID_DATE", "as_of must be ISO8601 with timezone")
    if when.tzinfo is None:
        raise DomainError("INVALID_DATE", "Timezone required")
    with LOCK:
        revision = g.revision()
        roots = g.read(Q1, {"decision_id": decision_id}, "Q1", trace)
        if not roots:
            raise DomainError(
                "NOT_FOUND", "Decision or verified CHANGES roots missing", 404
            )
        d = roots[0]
        if d["status"] not in ("proposed", "accepted"):
            raise DomainError(
                "INVALID_DECISION_STATE",
                "Only proposed or accepted decisions can be previewed",
                409,
            )
        if d["status"] == "proposed":
            old = g.read(
                "MATCH (d:Decision {id:$id}) RETURN d.status AS status",
                {"id": d["old_id"]},
                "PREVIOUS_DECISION",
                trace,
            )
            if not old or old[0]["status"] != "accepted":
                raise DomainError(
                    "INVALID_DECISION_STATE",
                    "Proposal requires an accepted comparison decision",
                    409,
                )
        paths = {}
        cycle_detected = False
        root_claims = {}
        edges = {}
        for root in roots:
            rid = root["root_id"]
            paths.setdefault(rid, set()).add(((rid,), ()))
            root_claims.setdefault(rid, []).append(root["claim_id"])
            for row in g.read(Q2, {"root_id": rid}, "Q2", trace):
                ids = tuple(row["service_path"])
                cycle_detected = cycle_detected or len(set(ids)) < len(ids)
                claims = tuple(row["claim_path"])
                paths.setdefault(row["service_id"], set()).add((ids, claims))
                for a, b, c in zip(ids, ids[1:], claims):
                    edges[c] = dict(source=a, target=b, claim_id=c)
        ids = sorted(paths)
        services = {
            r["id"]: r
            for r in g.read(
                "MATCH (s:Service) WHERE s.id IN $ids RETURN s.id AS id,s.name AS name,s.criticality AS criticality",
                {"ids": ids},
                "SERVICES",
                trace,
            )
        }
        drifts, review_date_issues = classify(g, d, ids, when, trace)
        impacts = []
        for ident, variants in paths.items():
            ordered = sorted(
                variants, key=lambda p: (len(p[0]), "|".join(p[0]), "|".join(p[1]))
            )
            kept = ordered[:3]
            depth = len(ordered[0][0]) - 1
            owners = ownership(g, ident, trace)
            ds = [x for x in drifts if ident in x["related_service_ids"]]
            score, priority = rank(
                depth,
                services[ident]["criticality"],
                owners["owner_status"],
                {x["tier"] for x in ds},
            )
            impacts.append(
                dict(
                    service_id=ident,
                    name=services[ident]["name"],
                    criticality=services[ident]["criticality"],
                    depth=depth,
                    paths=[list(p[0]) for p in kept],
                    path_claim_ids=[list(p[1]) for p in kept],
                    alternative_path_count=len(ordered),
                    score=score,
                    priority=priority,
                    **owners,
                    drift_ids=[x["id"] for x in ds],
                    evidence_ids=sorted(
                        set(
                            root_claims.get(ident, [])
                            + [c for _, cs in kept for c in cs]
                            + [o["claim_id"] for o in owners["ownership_claims"]]
                        )
                    ),
                )
            )
        impacts.sort(key=lambda x: (-x["score"], x["depth"], x["service_id"]))
        projects = g.read(Q3, {"affected_ids": ids}, "Q3", trace)
        boundary = [i["service_id"] for i in impacts if i["depth"] == 5]
        beyond = g.read(
            "MATCH (s:Service)-[:DEPENDS_ON]->(b:Service) WHERE b.id IN $boundary AND NOT s.id IN $ids RETURN DISTINCT s.id AS id",
            {"boundary": boundary, "ids": ids},
            "TRUNCATION",
            trace,
        )
        if g.revision() != revision:
            raise DomainError("STALE_ANALYSIS", "Graph changed during preview", 409)
        for t in trace:
            t["graph_revision"] = revision
        counts = dict(
            services=len(impacts),
            projects=len({p["project_id"] for p in projects}),
            **{f"drift_t{i}": sum(d["tier"] == i for d in drifts) for i in (1, 2, 3)},
            owner_gaps=sum(i["owner_status"] == "unowned" for i in impacts),
            owner_conflicts=sum(i["owner_status"] == "conflict" for i in impacts),
        )
        return dict(
            decision_id=decision_id,
            decision_status=d["status"],
            analysis_mode="preview",
            graph_revision=revision,
            as_of=as_of,
            max_hops=5,
            truncated=bool(beyond),
            counts=counts,
            impacts=impacts,
            projects=projects,
            drifts=drifts,
            query_trace=trace,
            source_mode="live_falkordb",
            roots=sorted({r["root_id"] for r in roots}),
            edges=list(edges.values()),
            decision=d,
            cycle_detected=cycle_detected,
            review_date_issues=review_date_issues,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )
