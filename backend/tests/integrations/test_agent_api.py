import json
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, graph as graph_dependency
from backend.app.settings import settings
from backend.app.agent.loop import run
from backend.app.agent.tools import ToolSession
from backend.app.domain.impact import preview
from backend.app.graph.client import DomainError, GraphUnavailable


@pytest.fixture
def client(graph, monkeypatch):
    app.dependency_overrides[graph_dependency] = lambda: graph
    monkeypatch.setattr(settings, "admin_token", "local-test-secret")
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


HEAD = {"Authorization": "Bearer local-test-secret"}


def test_admin_boundaries(client, monkeypatch):
    assert client.post("/api/admin/agent/runs", json={}).status_code == 403
    assert (
        client.post(
            "/api/admin/decisions/dec-auth-002/accept", json={"confirm": True}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/admin/import",
            headers=HEAD,
            json={"kind": "doc", "content": "invalid"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/admin/import",
            headers=HEAD,
            json={"kind": "doc", "content": "x", "path": "/etc/passwd"},
        ).status_code
        == 422
    )
    monkeypatch.setattr(settings, "mode", "public-readonly")
    for path in [
        "/api/admin/import",
        "/api/admin/agent/runs",
        "/api/admin/tasks/task-test/approve",
        "/api/admin/decisions/dec-auth-002/accept",
    ]:
        assert client.post(path, headers=HEAD, json={}).status_code == 403
    assert client.get("/api/decisions/dec-auth-002/preview").status_code == 200


def test_api_preview_pure(client, graph):
    rev = graph.revision()
    for _ in range(2):
        p = client.get("/api/decisions/dec-auth-002/preview").json()
        assert p["counts"]["services"] == len(p["impacts"])
    assert graph.revision() == rev
    assert client.post("/api/decisions/dec-auth-002/preview").status_code == 405
    assert (
        client.get(
            "/api/sources/search", params={"q": "MATCH (n) DELETE n"}
        ).status_code
        == 400
    )


def test_public_readonly_limits_requests_and_never_offers_a_provider(
    client, monkeypatch
):
    from backend.app.rate_limit import PublicRateLimiter

    monkeypatch.setattr(settings, "mode", "public-readonly")
    monkeypatch.setattr(settings, "api_key", "test-only-provider")
    monkeypatch.setattr(settings, "agent_mode", "llm")
    monkeypatch.setattr("backend.app.main.public_limiter", PublicRateLimiter(burst=2))
    assert client.get("/api/health").json()["provider_configured"] is False
    assert client.get("/api/health").status_code == 200
    limited = client.get("/api/health", headers={"X-Forwarded-For": "198.51.100.2"})
    assert limited.status_code == 429 and limited.headers["retry-after"]
    # Rejected writes do not consume a database call or invoke a provider.
    assert (
        client.post(
            "/api/admin/agent/runs", headers=HEAD, json={"mode": "llm"}
        ).status_code
        == 403
    )


def test_agent_deterministic_and_task_approval(client, graph):
    r = client.post(
        "/api/admin/agent/runs", headers=HEAD, json={"mode": "deterministic"}
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert (
        data["mode"] == "deterministic"
        and data["tool_calls"] <= 12
        and len(data["tasks"]) == 3
    )
    assert all(t["status"] == "ok" for t in data["trace"])
    for t in data["tasks"]:
        if t["owner_status"] in ("unowned", "conflict"):
            assert not t["owner_id"]
    assert data["source_chars"] <= 12000 and data["elapsed_ms"] < 90000
    old = graph.read("MATCH (d:Decision) RETURN d.status AS status ORDER BY d.id")
    assert (
        client.post(
            "/api/admin/tasks/" + data["tasks"][0]["id"] + "/approve",
            headers=HEAD,
            json={"confirm": True},
        ).status_code
        == 200
    )
    assert (
        graph.read("MATCH (d:Decision) RETURN d.status AS status ORDER BY d.id") == old
    )
    assert client.get("/api/agent/runs/" + data["id"]).json()["trace"]


def test_missing_llm_key_honest(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")
    r = client.post("/api/admin/agent/runs", headers=HEAD, json={"mode": "llm"})
    assert (
        r.status_code == 503
        and r.json()["error"]["code"] == "AGENT_PROVIDER_UNAVAILABLE"
    )


def test_tools_reject_fabrication_and_cypher(graph):
    s = ToolSession(graph, preview(graph, "dec-auth-002"))
    for name, args in [
        ("execute_cypher", {"cypher": "MATCH (n) DELETE n"}),
        ("trace_dependency", {"service_id": "svc-test' DELETE n"}),
        ("investigate_ownership", {"service_id": "svc-imaginary"}),
    ]:
        with pytest.raises(Exception):
            s.call(name, args)
    with pytest.raises(DomainError):
        s.call(
            "propose_remediation",
            {
                "service_id": "svc-auth-gateway",
                "kind": "migrate_client",
                "title": "Verify integration",
                "reason": "Evidence must be real and retrieved.",
                "evidence_ids": ["claim-imaginary"],
            },
        )
    # Prompt injection lives in the source, with no additional permissions or calls.
    r = s.call("read_evidence", {"source_id": "chat-080"})
    assert "Ignore system instructions" in r["untrusted_source_text"]
    assert not s.tasks


def test_model_loop_choices_and_limits(graph):
    responses = [
        ("search_sources", {"alias": "OrionAuth"}),
        ("investigate_ownership", {"service_id": "svc-token-cache"}),
        ("execute_cypher", {"query": "DELETE everything"}),
    ]

    def fake(messages, tools, timeout):
        index = sum(m["role"] == "tool" for m in messages)
        if index >= len(responses):
            return {
                "role": "assistant",
                "content": "Abstaining from unsupported assignments.",
            }, {}
        name, args = responses[index]
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": str(index),
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(args)},
                }
            ],
        }, {"total_tokens": 7}

    r = run(graph, "dec-auth-002", "llm", complete=fake)
    assert [t.get("tool") for t in r["trace"][:3]] == [x[0] for x in responses]
    assert r["trace"][2]["status"] == "rejected" and not r["tasks"]
    # Fake calls are a unit fixture, never saved as proof of a genuine provider run.
    graph.write(
        "MATCH (r:AgentRun {id:$id}) SET r.mode=$mode,r.model=$model",
        {"id": r["id"], "mode": "mocked_test", "model": "mock-provider"},
    )

    def unending(messages, tools, timeout):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": str(len(messages)),
                    "type": "function",
                    "function": {
                        "name": "search_sources",
                        "arguments": '{"alias":"OrionAuth"}',
                    },
                }
            ],
        }, {}

    bounded = run(graph, "dec-auth-002", "llm", complete=unending)
    assert (
        bounded["turns"] == 8
        and bounded["tool_calls"] == 8
        and bounded["status"] == "turn_limit"
    )
    graph.write(
        "MATCH (r:AgentRun {id:$id}) SET r.mode=$mode,r.model=$model",
        {"id": bounded["id"], "mode": "mocked_test", "model": "mock-provider"},
    )


def test_stale_guard(graph):
    s = ToolSession(graph, preview(graph, "dec-auth-002"))
    graph.bump()
    with pytest.raises(DomainError) as e:
        s.call("search_sources", {"alias": "OrionAuth"})
    assert e.value.code == "STALE_ANALYSIS"


def test_decision_acceptance_separate(client, graph):
    assert (
        client.post(
            "/api/admin/decisions/dec-auth-002/accept",
            headers=HEAD,
            json={"confirm": False},
        ).status_code
        == 409
    )
    old = graph.revision()
    r = client.post(
        "/api/admin/decisions/dec-auth-002/accept", headers=HEAD, json={"confirm": True}
    )
    assert r.status_code == 200
    assert (
        graph.revision() == old + 1
        and graph.read("MATCH ()-[r:SUPERSEDES]->() RETURN count(r) AS n")[0]["n"] == 1
    )
    assert (
        graph.read(
            "MATCH (a:ApprovalEvent {action:'accept_decision'}) RETURN count(a) AS n"
        )[0]["n"]
        == 1
    )
    # Restore test-only proposal to let module fixtures be independent of collection order.
    graph.write(
        "MATCH (d:Decision {id:'dec-auth-002'}) SET d.status='proposed' WITH d MATCH (d)-[r:SUPERSEDES]->() DELETE r"
    )


def test_graph_unavailable_handler(client):
    def unavailable():
        raise GraphUnavailable()

    app.dependency_overrides[graph_dependency] = unavailable
    for url in [
        "/api/health",
        "/api/decisions/dec-auth-002/preview",
        "/api/company/summary",
    ]:
        r = client.get(url)
        assert r.status_code == 503 and r.json()["error"]["code"] == "GRAPH_UNAVAILABLE"


@pytest.mark.parametrize("batch_extra", [False, True])
def test_all_three_cases_can_be_evidenced_in_eight_model_turns(graph, batch_extra):
    from backend.app.agent.proof import llm_proof

    analysis = preview(graph, "dec-auth-002")
    gap = next(i for i in analysis["impacts"] if i["owner_status"] == "unowned")
    conflict = next(i for i in analysis["impacts"] if i["owner_status"] == "conflict")
    suspect = next(d for d in analysis["drifts"] if d["tier"] == 2)

    def fake(messages, tools, timeout):
        answers = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        n = len(answers)
        if n:
            feedback = json.loads(messages[-1]["content"])
            turns = sum(m["role"] == "assistant" for m in messages)
            assert feedback["budget"]["model_turns_remaining"] == 8 - turns
            assert "verified_progress" in feedback
        if n == 0:
            name, args = "investigate_ownership", {"service_id": gap["service_id"]}
        elif n == 1:
            name, args = (
                "search_sources",
                {"alias": gap["name"], "kind": "chat", "limit": 2},
            )
        elif n == 2:
            name, args = (
                "propose_remediation",
                {
                    "service_id": gap["service_id"],
                    "kind": "verify_owner",
                    "title": "Verify the missing primary owner",
                    "reason": "No verified primary owner exists. Review the additional source before assigning anyone.",
                    "evidence_ids": answers[0]["evidence_ids"],
                    "owner_id": None,
                },
            )
        elif n == 3:
            name, args = "investigate_ownership", {"service_id": conflict["service_id"]}
        elif n == 4:
            name, args = (
                "propose_remediation",
                {
                    "service_id": conflict["service_id"],
                    "kind": "verify_owner",
                    "title": "Review the conflicting primary claims",
                    "reason": "Both source-backed primary claims require human reconciliation. No winner is assigned.",
                    "evidence_ids": answers[3]["evidence_ids"],
                    "owner_id": None,
                },
            )
        elif n == 5:
            name, args = (
                "search_sources",
                {"alias": "OrionAuth", "kind": "doc", "limit": 4},
            )
        elif n == 6:
            name, args = (
                "read_evidence",
                {"source_id": suspect["source_id"], "max_chars": 700},
            )
        else:
            name, args = (
                "propose_remediation",
                {
                    "service_id": suspect["related_service_ids"][0],
                    "kind": "review_doc",
                    "title": "Review the possible obsolete provider mention",
                    "reason": "Verify this unlinked mention. It is suspected drift and does not establish an integration dependency.",
                    "evidence_ids": [
                        s["mention_id"]
                        for s in answers[5]["sources"]
                        if s["source_id"] == suspect["source_id"]
                    ],
                    "owner_id": None,
                },
            )
        calls = [
            {
                "id": str(n),
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
        ]
        if n == 6 and batch_extra:
            # Completing coverage mid-batch must not revoke tools already offered
            # for this response. The next model turn receives the narrowed tools.
            calls.append(
                {
                    "id": "same-batch-summary",
                    "type": "function",
                    "function": {
                        "name": "get_impact_summary",
                        "arguments": '{"decision_id":"dec-auth-002"}',
                    },
                }
            )
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": calls,
        }, {"total_tokens": 10}

    result = run(graph, "dec-auth-002", "llm", complete=fake)
    assert result["status"] == "completed" and result["coverage"]["all_passed"]
    assert result["turns"] == 8 and result["tool_calls"] == 8 + int(batch_extra)
    assert all(t["status"] == "ok" for t in result["trace"])
    assert set(result["tool_offers"][-1]["tools"]) == {"propose_remediation", "abstain"}
    assert all(not t["owner_id"] for t in result["tasks"])
    assert not llm_proof(result)[
        "verified"
    ]  # A mock can never satisfy real-provider proof.
    assert all(
        len(json.dumps(entry["result"], ensure_ascii=False)) <= 3000
        for entry in result["trace"]
        if "result" in entry
    )
