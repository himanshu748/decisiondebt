"""Run the explicitly requested real investigation through the protected local API."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from backend.app.settings import ROOT, settings
from backend.app.agent.proof import llm_proof


def main():
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=100) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        if not health.json().get("provider_configured"):
            print(
                "The provider is not configured in the running server. Save DD_LLM_API_KEY and DD_AGENT_MODE=llm in .env, then restart the local API. No provider call was made."
            )
            return 2
        response = client.post(
            "/api/admin/agent/runs",
            headers={"Authorization": "Bearer " + settings.admin_token},
            json={"decision_id": "dec-auth-002", "mode": "llm"},
        )
        if response.status_code != 200:
            try:
                error = response.json().get("error", {})
            except ValueError:
                error = {
                    "code": "SERVER_ERROR",
                    "message": "Local API returned a non-JSON error. Inspect the private server log.",
                }
            print(
                json.dumps(
                    {
                        "status": response.status_code,
                        "code": error.get("code"),
                        "message": error.get("message"),
                    }
                )
            )
            return 2
        run = response.json()
        proof = llm_proof(run)
        destination = (
            ROOT
            / "evidence/agent-traces"
            / (
                "llm-run.json"
                if proof["verified"]
                else "llm-incomplete-" + run["id"] + ".json"
            )
        )
        destination.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n")
        (ROOT / "evidence/agent-traces/llm-proof.json").write_text(
            json.dumps(proof, indent=2) + "\n"
        )
        print(json.dumps(proof, indent=2))
        return 0 if proof["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
