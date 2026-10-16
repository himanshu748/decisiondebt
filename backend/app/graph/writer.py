"""All interpolated labels come from this fixed server-owned mapping."""

from backend.app.ingest.verify import RELATIONS


def persist_source(graph, source, claims):
    rev = (
        "rev-"
        + __import__("hashlib")
        .sha256((source.id + source.sha256).encode())
        .hexdigest()[:24]
    )
    old = graph.read(
        "MATCH (s:Source {id:$id}) RETURN s.sha256 AS sha256", {"id": source.id}
    )
    if old and old[0]["sha256"] == source.sha256:
        return {"id": source.id, "changed": False, "claims": 0}
    # Exactly this source's claim edges are retracted. Other parallel claim edges survive.
    graph.write(
        "MATCH (c:Claim {source_id:$id}) WHERE c.status <> $retracted WITH c MATCH ()-[r]->() WHERE r.claim_id=c.id DELETE r",
        {"id": source.id, "retracted": "retracted"},
    )
    graph.write(
        "MATCH (c:Claim {source_id:$id}) SET c.status='retracted'", {"id": source.id}
    )
    graph.write(
        "MATCH (s:Source {id:$id})-[a:ACTIVE_REVISION]->() DELETE a", {"id": source.id}
    )
    props = source.model_dump(exclude={"metadata", "raw_text"})
    props["active_revision"] = rev
    graph.write(
        "MERGE (s:Source {id:$id}) SET s += $props", {"id": source.id, "props": props}
    )
    revision_props = {
        "id": rev,
        "source_id": source.id,
        "sha256": source.sha256,
        "body": source.body,
        "raw_text": source.raw_text,
        "created_at": source.created_at,
    }
    graph.write(
        "MERGE (r:SourceRevision {id:$rev}) SET r += $props WITH r MATCH (s:Source {id:$id}) MERGE (s)-[:ACTIVE_REVISION]->(r)",
        {"rev": rev, "id": source.id, "props": revision_props},
    )
    meta = source.metadata
    if meta.get("decision_id"):
        decision = graph.read(
            "MATCH (d:Decision {id:$id}) RETURN d.status AS status",
            {"id": meta["decision_id"]},
        )
        if not decision:
            raise ValueError("Unknown decision ID")
        # Initial source may establish historical state. Subsequent source updates cannot perform acceptance.
        if decision[0]["status"] == "uninitialized":
            status = meta.get("decision_status")
            if status not in ("accepted", "proposed"):
                raise ValueError("Invalid initial decision state")
            props = {
                "title": source.title,
                "status": status,
                "created_at": source.created_at,
                "proposed_supersedes_id": meta.get("proposed_supersedes_id", ""),
                "obsolete_terms": meta.get("obsolete_terms", "").split(","),
                "source_id": source.id,
            }
            graph.write(
                "MATCH (d:Decision {id:$id}) SET d += $props",
                {"id": meta["decision_id"], "props": props},
            )
    for c in claims:
        props = c.model_dump()
        graph.write(
            "MERGE (c:Claim {id:$id}) SET c += $props WITH c MATCH (r:SourceRevision {id:$rev}) MERGE (c)-[:SUPPORTED_BY]->(r)",
            {"id": c.id, "props": props, "rev": rev},
        )
        if c.status != "verified":
            continue
        a, b = RELATIONS[c.relation]
        graph.write(
            f"MATCH (a:{a} {{id:$a}}),(b:{b} {{id:$b}}) MERGE (a)-[r:{c.relation} {{claim_id:$claim}}]->(b) SET r.role=$role",
            {
                "a": c.subject_id,
                "b": c.object_id,
                "claim": c.id,
                "role": "primary" if c.relation == "OWNS" else "",
            },
        )
    return {
        "id": source.id,
        "changed": True,
        "claims": len(claims),
        "verified": sum(c.status == "verified" for c in claims),
        "candidates": sum(c.status == "candidate" for c in claims),
    }
