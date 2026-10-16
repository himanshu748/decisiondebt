from backend.app.graph.client import LOCK
from redis.exceptions import ResponseError

LABELS = [
    "Service",
    "Person",
    "Team",
    "Project",
    "Decision",
    "Source",
    "SourceRevision",
    "Claim",
    "Task",
    "AgentRun",
    "ApprovalEvent",
]


def initialize(graph, catalog):
    def ensure(query):
        try:
            graph.write(query)
        except ResponseError as e:
            if "already indexed" not in str(e):
                raise

    with LOCK:
        for label in LABELS:
            ensure(f"CREATE INDEX FOR (n:{label}) ON (n.id)")
        ensure("CREATE INDEX FOR (n:Meta) ON (n.key)")
        try:
            graph.write("CREATE FULLTEXT INDEX FOR (s:Source) ON (s.title, s.body)")
        except ResponseError as e:
            if "already indexed" not in str(e):
                raise
        graph.write("MERGE (m:Meta {key:'graph_revision'}) ON CREATE SET m.value=0")
        for e in catalog.entities:
            label = e["label"]
            if label not in LABELS:
                raise ValueError("Invalid label")
            props = {k: v for k, v in e.items() if k != "label"}
            if label == "Decision":
                props["status"] = "uninitialized"
            graph.write(
                f"MERGE (n:{label} {{id:$id}}) ON CREATE SET n += $props",
                {"id": e["id"], "props": props},
            )
