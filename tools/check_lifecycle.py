"""Explicit local-only outage/restart proof for the dedicated DecisionDebt container."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from backend.app.settings import ROOT, settings
from backend.app.graph.client import Graph, GraphUnavailable
from backend.app.domain.company import summary

if __name__ == "__main__":
    receipt = {}
    container = os.getenv("DD_TEST_DB_CONTAINER", "decisiondebt-db")
    receipt_path = Path(
        os.getenv("DD_LIFECYCLE_RECEIPT", ROOT / "work/test-evidence/lifecycle.json")
    )
    client = httpx.Client(
        base_url=os.getenv("DD_TEST_API_URL", "http://127.0.0.1:8000"), timeout=45
    )
    before = summary(Graph())
    receipt["before"] = before
    try:
        subprocess.run(["docker", "stop", container], check=True, capture_output=True)
        for path, method in [
            ("/api/decisions/dec-auth-002/preview", "GET"),
            ("/api/admin/agent/runs", "POST"),
        ]:
            r = (
                client.get(path)
                if method == "GET"
                else client.post(
                    path,
                    headers={"Authorization": "Bearer " + settings.admin_token},
                    json={"mode": "deterministic"},
                )
            )
            receipt[path] = {"status": r.status_code, "body": r.json()}
            assert (
                r.status_code == 503
                and r.json()["error"]["code"] == "GRAPH_UNAVAILABLE"
            )
    finally:
        subprocess.run(["docker", "start", container], check=True, capture_output=True)
    for _ in range(40):
        try:
            Graph().health()
            break
        except GraphUnavailable:
            time.sleep(0.25)
    after = summary(Graph())
    receipt["after"] = after
    assert (
        after["counts"] == before["counts"]
        and after["graph_revision"] == before["graph_revision"]
    )
    receipt["persistence_passed"] = True
    receipt["image"] = subprocess.check_output(
        [
            "docker",
            "image",
            "inspect",
            "falkordb/falkordb:6.0.2",
            "--format",
            "{{json .RepoDigests}} {{.Architecture}}",
        ],
        text=True,
    ).strip()
    receipt["aof"] = subprocess.check_output(
        [
            "docker",
            "exec",
            container,
            "redis-cli",
            "CONFIG",
            "GET",
            "appendonly",
        ],
        text=True,
    ).strip()
    smoke = Graph("decisiondebt_smoke").read(
        "MATCH (s:Source {id:'smoke'}) RETURN s.body AS body"
    )
    assert smoke and smoke[0]["body"] == "Verified synthetic persistence marker"
    receipt["smoke_marker_persisted"] = True
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
