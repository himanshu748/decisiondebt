"""Read-only submission audit. It never deploys, pushes, approves or invokes a model."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.settings import ROOT
from backend.app.graph.client import Graph
from backend.app.domain.company import summary
from backend.app.domain.impact import preview
from backend.app.domain.evidence import claim_evidence


def verify():
    checks = {}
    limitations = []
    required = [
        "README.md",
        "DECISIONS.md",
        "LEARNING.md",
        "DEMO.md",
        "spec.md",
        "prd.md",
        "CODEX_INITIAL_PROMPT.md",
        "compose.yaml",
        "requirements.txt",
        "web/package-lock.json",
        "evidence/screenshots/desktop-preview.png",
        "evidence/screenshots/mobile-preview.png",
        "evidence/decisiondebt-demo.mp4",
        "evidence/agent-traces/deterministic.json",
        "evidence/test-results/lifecycle.json",
        "evidence/query-results/dynamic-import.json",
    ]
    checks["required_files"] = all(
        (ROOT / p).is_file() and (ROOT / p).stat().st_size > 0 for p in required
    )
    missing = [p for p in required if not (ROOT / p).is_file()]
    broken = []
    for doc in ["README.md", "DECISIONS.md", "LEARNING.md", "DEMO.md"]:
        for link in re.findall(r"\]\(([^)]+)\)", (ROOT / doc).read_text()):
            if (
                not link.startswith(("http:", "https:", "#"))
                and not (ROOT / link.split("#")[0]).exists()
            ):
                broken.append(f"{doc}: {link}")
    checks["local_document_links"] = not broken
    graph = Graph()
    s = summary(graph)
    p = preview(graph, "dec-auth-002")
    checks["corpus_graph"] = (
        s["counts"]["service"] == 60
        and s["counts"]["source"] >= 90
        and s["counts"]["semantic_edges"] >= 100
    )
    checks["proposed_preview"] = p["decision_status"] == "proposed"
    before = graph.revision()
    preview(graph, "dec-auth-002")
    checks["preview_readonly"] = (
        graph.revision() == before
        and not graph.read("MATCH ()-[r:SUPERSEDES]->() RETURN count(r) AS n")[0]["n"]
    )
    active = graph.read(
        "MATCH ()-[r]->() WHERE r.claim_id IS NOT NULL RETURN r.claim_id AS id"
    )
    checks["all_active_edges_anchored"] = all(
        claim_evidence(graph, r["id"])["anchor_verified"] for r in active
    )
    checks["three_drift_tiers"] = {d["tier"] for d in p["drifts"]} == {1, 2, 3}
    checks["owner_ambiguities"] = (
        p["counts"]["owner_gaps"] >= 1 and p["counts"]["owner_conflicts"] >= 1
    )
    score = json.loads(
        (ROOT / "evidence/test-results/precision-recall.json").read_text()
    )
    checks["precision_recall"] = score["precision"] == 1 and score["recall"] >= 0.95
    log = (ROOT / "evidence/test-results/pytest.txt").read_text()
    test_result = re.search(r"(\d+) passed", log)
    checks["pytest"] = bool(test_result) and not re.search(
        r"\d+ (failed|errors?)\b", log
    )
    ui = json.loads((ROOT / "evidence/test-results/ui-smoke.json").read_text())
    checks["browser"] = (
        ui["count_matches"]
        and ui["no_horizontal_overflow"]
        and not ui["console_errors"]
    )
    lifecycle = json.loads((ROOT / "evidence/test-results/lifecycle.json").read_text())
    checks["outage_persistence"] = (
        lifecycle["persistence_passed"]
        and lifecycle["smoke_marker_persisted"]
        and all(
            lifecycle[path]["status"] == 503
            for path in ["/api/decisions/dec-auth-002/preview", "/api/admin/agent/runs"]
        )
    )
    path = ROOT / "evidence/query-results/dynamic-import.json"
    if path.exists():
        dynamic = json.loads(path.read_text())
        checks["dynamic_import_retraction"] = (
            dynamic["after"]["counts"]["services"]
            == dynamic["before"]["counts"]["services"] + 1
            and dynamic["reverted"]["counts"]["services"]
            == dynamic["before"]["counts"]["services"]
        )
    else:
        checks["dynamic_import_retraction"] = False
    llm = graph.read(
        "MATCH (r:AgentRun {mode:'llm'}) RETURN r.id AS id,r.status AS status"
    )
    if not llm:
        limitations.append(
            "No genuine LLM provider trace. The included investigation is explicitly deterministic."
        )
    limitations.extend(
        [
            "No remote push, public deployment or portal submission was performed.",
            "Single API worker only; CLI ingestion requires API stopped.",
            "Extraction accuracy is measured on the synthetic fixture, not arbitrary enterprise language.",
        ]
    )
    report = dict(
        status="local_checks_pass" if all(checks.values()) else "incomplete",
        checks=checks,
        missing=missing,
        broken_links=broken,
        pytest_passed=int(test_result[1]) if test_result else 0,
        live_summary=s,
        preview_counts=p["counts"],
        max_hops=p["max_hops"],
        truncated=p["truncated"],
        precision_recall=score,
        limitations=limitations,
    )
    (ROOT / "evidence/submission-report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(verify())
