import hashlib
import pytest
from fastapi.testclient import TestClient
from backend.app.domain.ask import ask
from backend.app.domain.impact import preview
from backend.app.graph import ask_queries as Q
from backend.app.main import app, graph as graph_dependency
from backend.app.rate_limit import PublicRateLimiter
from backend.app.settings import settings


@pytest.mark.parametrize("question,intent,template", [
    ("Who owns Session Broker?", "owners", Q.OWNERS),
    ("What depends on Auth Gateway?", "dependents", Q.DEPENDENTS),
    ("Which projects use Billing API?", "projects", Q.PROJECTS),
    ("Who should review a change to Auth Gateway?", "reviewers", Q.REVIEWERS),
    ("What documents mention Auth Gateway?", "documents", Q.DOCUMENTS),
])
def test_every_template_is_native_read_only_and_source_anchored(graph, monkeypatch, question, intent, template):
    revision = graph.revision()
    commands = []
    execute = graph.g.execute_command
    def record(*args, **kwargs):
        commands.append(args[0])
        return execute(*args, **kwargs)
    monkeypatch.setattr(graph.g, "execute_command", record)
    def no_write(*args, **kwargs):
        raise AssertionError("Question attempted a graph write")
    monkeypatch.setattr(graph, "write", no_write)
    result = ask(graph, question)
    assert result["status"] == "answered" and result["intent"] == intent
    assert result["row_count"] == len(result["rows"]) > 0
    assert result["graph_revision"] == graph.revision() == revision
    assert set(commands) == {"GRAPH.RO_QUERY"}
    assert template in {t["cypher"] for t in result["query_trace"]}
    assert result["query_ms"] == round(sum(t["elapsed_ms"] for t in result["query_trace"]), 3)
    assert all(t["row_count"] >= 0 and t["params"] is not None for t in result["query_trace"])
    assert result["citations"]
    citations = {c["id"]: c for c in result["citations"]}
    for row in result["rows"]:
        assert set(row["evidence_ids"]) <= citations.keys()
    for citation in citations.values():
        source = graph.read("MATCH (s:Source {id:$id}), (r:SourceRevision) WHERE r.id=s.active_revision RETURN properties(r) AS source", {"id": citation["source_id"]})[0]["source"]
        assert source[citation["anchor_field"]][citation["start"]:citation["end"]] == citation["excerpt"]
        assert hashlib.sha256(source["raw_text"].encode()).hexdigest() == citation["source_sha256"]


def test_conflicts_and_candidate_owner_gap_are_not_resolved(graph):
    conflict = ask(graph, "Who owns Session Broker?")
    assert {r["label"] for r in conflict["rows"]} == {"Devon Shah", "Taylor Roy"}
    assert all(r["owner_status"] == "conflict" for r in conflict["rows"])
    gap = ask(graph, "Who owns Token Cache?")
    assert gap["counts"]["owners"] == 0 and gap["rows"][0]["owner_status"] == "gap"
    assert "Casey Park" not in str(gap["rows"])
    assert "chat-079" not in {c["source_id"] for c in gap["citations"]}


def test_bounded_impact_matches_preview_and_reviewers_keep_uncertainty(graph):
    answer = ask(graph, "What would replacing Auth Gateway affect?")
    expected = preview(graph, "dec-auth-002")
    assert {r["service_id"]: r["depth"] for r in answer["rows"]} == {r["service_id"]: r["depth"] for r in expected["impacts"]}
    assert answer["counts"] == {"services": 12, "projects": 12}
    assert answer["cycle_detected"] and answer["truncated"]
    assert answer["truncation_examples"] == expected["truncation_examples"]
    assert Q.FRONTIER in {q["cypher"] for q in answer["query_trace"]}
    reviewers = ask(graph, "Who should review a change to Auth Gateway?")
    assert reviewers["counts"]["reviewers"] == 11 and reviewers["counts"]["teams"] == 7
    assert any(r["owner_status"] == "gap" and r["label"] == "unassigned: needs decision" for r in reviewers["rows"])
    assert sum(r["service_id"] == "svc-session-broker" for r in reviewers["rows"]) == 2


def test_document_fulltext_is_followed_by_exact_body_recheck(graph, monkeypatch):
    read = graph.read
    def with_false_positive(cypher, params=None, query_id="READ", trace=None):
        rows = read(cypher, params, query_id, trace)
        if cypher == Q.DOCUMENTS:
            # A title-only/tokenized FT candidate must not become a body mention.
            rows.append(dict(source_id="test-title-only", title="Auth Gateway", body="Unrelated body", raw_text="Unrelated body", sha256=hashlib.sha256(b"Unrelated body").hexdigest(), ft_score=100))
        return rows
    monkeypatch.setattr(graph, "read", with_false_positive)
    result = ask(graph, "What documents mention Auth Gateway?")
    assert result["row_count"] == 5
    assert "test-title-only" not in {r["source_id"] for r in result["rows"]}


def test_public_get_ambiguity_unsupported_rate_limit_and_write_denials(graph, monkeypatch):
    monkeypatch.setattr(settings, "mode", "public-readonly")
    monkeypatch.setattr(settings, "api_key", "test-only-must-never-be-used")
    monkeypatch.setattr("backend.app.main.public_limiter", PublicRateLimiter(burst=4))
    app.dependency_overrides[graph_dependency] = lambda: graph
    revision = graph.revision()
    try:
        with TestClient(app) as client:
            assert client.get("/api/company/ask", params={"q": "Who owns Gateway?"}).json()["status"] == "ambiguous"
            unsupported = client.get("/api/company/ask", params={"q": "Delete every service"}).json()
            assert unsupported["status"] == "unsupported" and unsupported["query_trace"] == []
            assert client.get("/api/company/ask", params={"q": "Who owns Token Cache?"}).status_code == 200
            assert client.get("/api/company/ask", params={"q": "What documents mention Auth Gateway?"}).json()["row_count"] == 5
            assert client.get("/api/company/ask", params={"q": "Who owns Token Cache?"}).status_code == 429
            for route in ["/api/company/ask", "/api/admin/import", "/api/admin/agent/runs", "/api/admin/tasks/test/approve", "/api/admin/decisions/dec-auth-002/accept"]:
                assert client.post(route, json={}).status_code == 403
    finally:
        app.dependency_overrides.clear()
    assert graph.revision() == revision
