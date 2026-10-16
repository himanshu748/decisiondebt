from time import perf_counter
from backend.app.graph.client import LOCK


def summary(g):
    start = perf_counter()
    with LOCK:
        counts = {}
        for label in [
            "Service",
            "Person",
            "Team",
            "Project",
            "Source",
            "SourceRevision",
            "Claim",
            "Task",
            "Decision",
        ]:
            counts[label.lower()] = g.read(
                f"MATCH (n:{label}) RETURN count(n) AS count"
            )[0]["count"]
        counts["semantic_edges"] = g.read(
            "MATCH ()-[r]->() WHERE r.claim_id IS NOT NULL RETURN count(r) AS count"
        )[0]["count"]
        kinds = g.read(
            "MATCH (s:Source) RETURN s.kind AS kind,count(s) AS count ORDER BY kind"
        )
        statuses = g.read(
            "MATCH (c:Claim) RETURN c.status AS status,count(c) AS count ORDER BY status"
        )
        return dict(
            counts=counts,
            source_types=kinds,
            claim_statuses=statuses,
            graph_revision=g.revision(),
            synthetic=True,
            source_mode="live_falkordb",
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
        )


def topology(g):
    with LOCK:
        nodes = g.read(
            "MATCH (s:Service) RETURN s.id AS id,s.name AS name,s.criticality AS criticality ORDER BY id"
        )
        edges = g.read(
            "MATCH (a:Service)-[r:DEPENDS_ON]->(b:Service) RETURN a.id AS source,b.id AS target,r.claim_id AS claim_id"
        )
        return dict(
            nodes=nodes,
            edges=edges,
            graph_revision=g.revision(),
            source_mode="live_falkordb",
        )
