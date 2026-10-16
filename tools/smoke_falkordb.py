import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.graph.client import Graph

if __name__ == "__main__":
    g = Graph("decisiondebt_smoke")
    g.write("MATCH (n) DETACH DELETE n")
    try:
        g.write("DROP FULLTEXT INDEX FOR (s:Source) ON (s.title, s.body)")
    except Exception:
        pass
    print(
        json.dumps(
            {
                "host_architecture": platform.machine(),
                "write": g.write(
                    "MERGE (s:Source {id:'smoke'}) SET s.title='OrionAuth smoke',s.body='Verified synthetic persistence marker' RETURN s.id"
                ).result_set,
                "read": g.read("MATCH (s:Source) RETURN s.id AS id"),
                "index": g.write(
                    "CREATE FULLTEXT INDEX FOR (s:Source) ON (s.title, s.body)"
                ).result_set,
                "fulltext": g.read(
                    "CALL db.idx.fulltext.queryNodes('Source',$q) YIELD node, score RETURN node.id AS id, score",
                    {"q": "OrionAuth"},
                ),
            },
            indent=2,
            default=str,
        )
    )
