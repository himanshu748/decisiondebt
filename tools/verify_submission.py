"""Read-only submission audit. It never deploys, pushes, approves or invokes a model."""

import json
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.settings import ROOT
from backend.app.graph.client import Graph
from backend.app.domain.company import summary
from backend.app.domain.impact import preview
from backend.app.domain.evidence import claim_evidence
from backend.app.agent.proof import llm_proof


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
        "evidence/screenshots/landing-desktop.png",
        "evidence/screenshots/landing-mobile.png",
        "web/public/assets/knowledge-still-life.webp",
        "evidence/decisiondebt-demo.mp4",
        "evidence/agent-traces/deterministic.json",
        "evidence/test-results/lifecycle.json",
        "evidence/query-results/dynamic-import.json",
        "evidence/agent-traces/llm-run.json",
        "evidence/agent-traces/llm-proof.json",
        "evidence/demo-v2/manifest.json",
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
    runs = graph.read(
        "MATCH (r:AgentRun {mode:'llm'}) RETURN properties(r) AS run ORDER BY r.started_at DESC"
    )
    proofs = []
    for row in runs:
        run = row["run"]
        for key in ("coverage", "provider_calls"):
            if key + "_json" in run:
                run[key] = json.loads(run[key + "_json"])
        proofs.append(llm_proof(run))
    llm = next((p for p in proofs if p["verified"]), None)
    recorded = json.loads((ROOT / "evidence/agent-traces/llm-run.json").read_text())
    recorded_proof = llm_proof(recorded)
    checks["recorded_provider_proof"] = (
        recorded_proof["verified"]
        and llm is not None
        and recorded_proof["run_id"] == llm["run_id"]
        and recorded_proof
        == json.loads((ROOT / "evidence/agent-traces/llm-proof.json").read_text())
    )
    demo = json.loads((ROOT / "evidence/demo-v2/manifest.json").read_text())
    video = json.loads((ROOT / "evidence/test-results/video-metadata.json").read_text())
    v = next(s for s in video["streams"] if s["codec_type"] == "video")
    checks["recorded_demo"] = (
        demo["run_id"] == recorded_proof["run_id"]
        and demo["investigation"] == "genuine recorded provider run"
        and demo["continuous_native_recording"] is False
        and float(video["format"]["duration"]) == 90
        and v["width"] == 1280
        and v["height"] == 960
        and v["r_frame_rate"] == "30/1"
        and any(s["codec_type"] == "subtitle" for s in video["streams"])
        and all(
            hashlib.sha256((ROOT / f["path"]).read_bytes()).hexdigest() == f["sha256"]
            for f in demo["frames"]
        )
    )
    if not llm:
        limitations.append(
            "No genuine provider run covering all three ambiguity cases passed the proof gate."
        )
    limitations.extend(
        [
            "No public deployment or portal submission was performed. Repository publication is a separate Git operation.",
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
        llm=llm
        or {
            "verified": False,
            "status": "unverified",
            "attempts": proofs,
        },
        demo={
            "path": "evidence/decisiondebt-demo.mp4",
            "ui_version": demo["ui_version"],
            "investigation": demo["investigation"],
            "format": demo["format"],
            "continuous_native_recording": demo["continuous_native_recording"],
            "run_id": demo["run_id"],
            "duration_seconds": float(video["format"]["duration"]),
            "resolution": [v["width"], v["height"]],
            "fps": v["r_frame_rate"],
        },
        limitations=limitations,
    )
    (ROOT / "evidence/submission-report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(verify())
