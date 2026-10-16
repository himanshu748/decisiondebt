import json
from datetime import datetime, timezone
from backend.app.graph.client import LOCK, DomainError


def save_run(g, run, tasks, revision):
    with LOCK:
        if g.revision() != revision:
            raise DomainError(
                "STALE_ANALYSIS", "Graph changed before task persistence", 409
            )
        now = datetime.now(timezone.utc).isoformat()
        for task in tasks.values():
            task = {**task, "created_at": now}
            prior = g.read(
                "MATCH (t:Task {decision_id:$decision_id,service_id:$service_id,kind:$kind}) RETURN t.id AS id ORDER BY t.analysis_revision DESC LIMIT 1",
                {
                    "decision_id": task["decision_id"],
                    "service_id": task["service_id"],
                    "kind": task["kind"],
                },
            )
            if prior and prior[0]["id"] != task["id"]:
                task["previous_task_id"] = prior[0]["id"]
            g.write(
                "MERGE (t:Task {id:$id}) ON CREATE SET t += $props WITH t MATCH (s:Service {id:$service}) MERGE (t)-[:AFFECTS]->(s)",
                {"id": task["id"], "props": task, "service": task["service_id"]},
            )
            for ident in task["evidence_ids"]:
                if ident.startswith("claim-"):
                    g.write(
                        "MATCH (t:Task {id:$task}),(c:Claim {id:$claim}) MERGE (t)-[:CITES]->(c)",
                        {"task": task["id"], "claim": ident},
                    )
        props = {k: v for k, v in run.items() if k != "trace"}
        props["trace_json"] = json.dumps(run["trace"], ensure_ascii=False)
        g.write("CREATE (r:AgentRun) SET r += $props", {"props": props})
        g.bump()
        return {**run, "tasks": list(tasks.values()), "saved_revision": g.revision()}
