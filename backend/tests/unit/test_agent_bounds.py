import json
from backend.app.agent.bounds import bounded_result, references
from backend.app.agent.proof import llm_proof


def test_tool_output_is_structured_and_preserves_evidence_ids():
    sources = [
        {
            "source_id": f"doc-{i:03}",
            "kind": "doc",
            "context": "x" * 3000,
            "mention_id": f"mention:doc-{i:03}:abc:0:9",
            "title": "Context",
        }
        for i in range(20)
    ]
    result = bounded_result("search_sources", {"sources": sources})
    assert len(json.dumps(result, ensure_ascii=False)) <= 3000
    assert result["truncated"] and result["sources"]
    assert references(result) == {s["mention_id"] for s in result["sources"]}


def test_two_owner_claims_survive_bounding():
    result = bounded_result(
        "investigate_ownership",
        {
            "evidence": [
                {"id": "claim-one", "source_id": "doc-001", "excerpt": "a" * 5000},
                {"id": "claim-two", "source_id": "doc-002", "excerpt": "b" * 5000},
            ]
        },
    )
    assert {e["id"] for e in result["evidence"]} == {"claim-one", "claim-two"}
    assert all(len(e["excerpt"]) == 200 for e in result["evidence"])


def test_failed_or_fabricated_llm_run_does_not_count_as_proof():
    assert not llm_proof(
        {"mode": "llm", "status": "completed", "provider_verified": False}
    )["verified"]
