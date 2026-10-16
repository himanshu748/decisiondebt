"""Export synthetic app state and seed a separate, empty public graph without a provider call."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.graph.client import Graph
from backend.app.graph.schema import LABELS
from backend.app.settings import settings


def export_snapshot(destination):
    graph = Graph()
    revision = graph.revision()
    nodes = graph.read(
        "MATCH (n) RETURN id(n) AS key,labels(n) AS labels,properties(n) AS props"
    )
    edges = graph.read(
        "MATCH (a)-[r]->(b) RETURN id(a) AS source,id(b) AS target,type(r) AS relation,properties(r) AS props"
    )
    if graph.revision() != revision:
        raise RuntimeError(
            "Graph changed during export; retry without concurrent writes"
        )
    data = {
        "synthetic": True,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source_graph": settings.graph_name,
        "graph_revision": revision,
        "nodes": nodes,
        "edges": edges,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return {
        "path": str(destination),
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "nodes": len(nodes),
        "edges": len(edges),
        "graph_revision": revision,
    }


def import_snapshot(source):
    if settings.graph_name != "decisiondebt_public":
        raise RuntimeError(
            "Snapshot import is restricted to the separate decisiondebt_public graph"
        )
    data = json.loads(source.read_text())
    if data.get("synthetic") is not True:
        raise ValueError("Only a synthetic snapshot is accepted")
    allowed_labels = set(LABELS) | {"Meta"}
    for node in data["nodes"]:
        if not node["labels"] or not set(node["labels"]) <= allowed_labels:
            raise ValueError("Unexpected node label")
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", e["relation"]) for e in data["edges"]):
        raise ValueError("Unexpected relationship type")
    graph = Graph()
    existing = graph.db.connection.execute_command("GRAPH.LIST")
    existing = [name.decode() if isinstance(name, bytes) else name for name in existing]
    if (
        settings.graph_name in existing
        and graph.read("MATCH (n) RETURN count(n) AS count")[0]["count"]
    ):
        raise RuntimeError("Public graph is not empty; no existing state was changed")
    graph.write("CREATE INDEX FOR (n:_Snapshot) ON (n._snapshot_id)")
    for node in data["nodes"]:
        labels = ":".join(["_Snapshot", *node["labels"]])
        graph.write(
            f"CREATE (n:{labels}) SET n += $props,n._snapshot_id=$key",
            {"props": node["props"], "key": node["key"]},
        )
    for edge in data["edges"]:
        graph.write(
            f"MATCH (a:_Snapshot {{_snapshot_id:$source}}),(b:_Snapshot {{_snapshot_id:$target}}) CREATE (a)-[r:{edge['relation']}]->(b) SET r += $props",
            edge,
        )
    graph.write("MATCH (n:_Snapshot) REMOVE n._snapshot_id,n:_Snapshot")
    graph.write("DROP INDEX FOR (n:_Snapshot) ON (n._snapshot_id)")
    for label in LABELS:
        graph.write(f"CREATE INDEX FOR (n:{label}) ON (n.id)")
    graph.write("CREATE INDEX FOR (n:Meta) ON (n.key)")
    graph.write("CREATE FULLTEXT INDEX FOR (s:Source) ON (s.title,s.body)")
    return {
        "status": "seeded_recorded_synthetic_snapshot",
        "graph": settings.graph_name,
        "graph_revision": graph.revision(),
        "nodes": len(data["nodes"]),
        "edges": len(data["edges"]),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "provider_calls": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "import"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            export_snapshot(args.path)
            if args.action == "export"
            else import_snapshot(args.path),
            indent=2,
        )
    )
