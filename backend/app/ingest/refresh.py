from backend.app.graph.client import LOCK
from backend.app.graph.writer import persist_source
from backend.app.ingest.extract import extract


def refresh(graph, sources, catalog):
    # Validate every source and claim before writing any source in a batch.
    prepared = []
    seen = set()
    for src in sources:
        if src.id in seen:
            raise ValueError("Duplicate source ID")
        seen.add(src.id)
        if src.author_id not in catalog.by_id:
            raise ValueError("Unknown author")
        if (
            src.metadata.get("decision_id")
            and catalog.by_id.get(src.metadata["decision_id"], {}).get("label")
            != "Decision"
        ):
            raise ValueError("Unknown decision")
        prepared.append((src, extract(src, catalog)))
    with LOCK:
        result = [persist_source(graph, s, c) for s, c in prepared]
        if any(r["changed"] for r in result):
            graph.bump()
        return {
            "sources": result,
            "graph_revision": graph.revision(),
            "changed": sum(r["changed"] for r in result),
        }
