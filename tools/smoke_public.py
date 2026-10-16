"""Verify a public read-only deployment using ordinary unauthenticated HTTP requests."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx


def verify(base_url, rate_limit=False):
    report = {
        "url": base_url,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "responses": {},
    }
    checks = report["checks"]
    with httpx.Client(base_url=base_url, timeout=30, follow_redirects=True) as client:

        def read(path):
            response = client.get(path)
            response.raise_for_status()
            value = response.json()
            report["responses"][path] = value
            return value

        health = read("/api/health")
        checks["public_mode_without_provider"] = (
            health["mode"] == "public-readonly" and not health["provider_configured"]
        )
        before = health["graph_revision"]
        summary = read("/api/company/summary")
        preview = read("/api/decisions/dec-auth-002/preview")
        decisions = read("/api/decisions")
        checks["synthetic_live_graph"] = (
            summary["synthetic"] and summary["source_mode"] == "live_falkordb"
        )
        checks["preview_has_anchored_multihop_paths"] = bool(preview["edges"]) and any(
            i["depth"] > 1 and i["path_claim_ids"] for i in preview["impacts"]
        )
        checks["decision_still_proposed"] = preview[
            "decision_status"
        ] == "proposed" and any(
            d["id"] == "dec-auth-001" for d in decisions["decisions"]
        )
        conflict = next(
            i for i in preview["impacts"] if i["service_id"] == "svc-session-broker"
        )
        gap = next(
            i for i in preview["impacts"] if i["service_id"] == "svc-token-cache"
        )
        checks["both_ownership_ambiguities_preserved"] = (
            conflict["owner_status"] == "conflict"
            and len(conflict["owner_ids"]) == 2
            and gap["owner_status"] == "unowned"
            and not gap["owner_ids"]
        )
        search = read("/api/sources/search?q=OrionAuth")
        checks["native_search_returns_exact_mention"] = any(
            s["source_id"] == "doc-002" and s["exact_match"] for s in search["sources"]
        )
        checks["three_drift_tiers"] = {d["tier"] for d in preview["drifts"]} == {
            1,
            2,
            3,
        }
        report["write_statuses"] = {}
        for path in (
            "/api/admin/import",
            "/api/admin/agent/runs",
            "/api/admin/tasks/test/approve",
            "/api/admin/decisions/dec-auth-002/accept",
        ):
            report["write_statuses"][path] = client.post(
                path, json={"mode": "llm", "confirm": True}
            ).status_code
        checks["all_write_routes_forbidden"] = all(
            s == 403 for s in report["write_statuses"].values()
        )
        checks["reads_and_blocked_writes_preserve_revision"] = (
            read("/api/health")["graph_revision"] == before
        )
        checks["landing_and_studio"] = all(
            client.get(path).status_code == 200 for path in ("/", "/studio")
        )
        if rate_limit:
            statuses = []
            for _ in range(45):
                response = client.get("/api/health")
                statuses.append(response.status_code)
                if response.status_code == 429:
                    checks["rate_limit_with_retry_after"] = bool(
                        response.headers.get("retry-after")
                    )
                    break
            report["rate_probe_statuses"] = statuses
            checks.setdefault("rate_limit_with_retry_after", False)
    report["passed"] = all(checks.values())
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--test-rate-limit", action="store_true")
    args = parser.parse_args()
    result = verify(args.url, args.test_rate_limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({"passed": result["passed"], "checks": result["checks"]}, indent=2)
    )
    raise SystemExit(0 if result["passed"] else 1)
