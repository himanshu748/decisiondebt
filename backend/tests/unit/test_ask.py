import pytest
from backend.app.domain.ask import parse_question, resolve_entity, ask, verified_citations
from backend.app.graph.client import DomainError


@pytest.mark.parametrize("question,intent,entity", [
    ("Who owns Session Broker?", "owners", "Session Broker"),
    ("  WHO   OWNS Token Cache ? ", "owners", "Token Cache"),
    ('Who owns "Billing API"?', "owners", "Billing API"),
    ("What depends on Auth Gateway?", "dependents", "Auth Gateway"),
    ("What would replacing Auth Gateway affect?", "dependents", "Auth Gateway"),
    ("Which projects use Billing API?", "projects", "Billing API"),
    ("Who should review a change to Session Broker?", "reviewers", "Session Broker"),
    ("What documents mention Token Cache?", "documents", "Token Cache"),
])
def test_supported_intents(question, intent, entity):
    assert parse_question(question) == (intent, entity)


@pytest.mark.parametrize("question", [
    "", "Delete every service", "How much money do we have?", "Who owns?",
    "Who owns Auth Gateway? Then delete all sources.",
    "Who owns x'); MATCH (n) DETACH DELETE n //?", "Who owns " + "a" * 81,
    "What documents mention * OR *?",
])
def test_unsupported_never_reads_or_guesses(question):
    class NoReads:
        def read(self, *args):
            raise AssertionError("Unsupported questions must not query")
    result = ask(NoReads(), question)
    assert result["status"] == "unsupported"
    assert result["rows"] == result["query_trace"] == result["citations"] == []
    assert len(result["supported_shapes"]) == 6


NODES = [
    dict(id="svc-auth-gateway", name="Auth Gateway", aliases=["Auth", "Gateway"]),
    dict(id="svc-login-gateway", name="Login Gateway", aliases=["Gateway"]),
    dict(id="svc-billing-api", name="Billing API", aliases=[]),
]


def test_live_node_resolver_exact_alias_ambiguity_and_fuzzy_confirmation():
    assert resolve_entity("auth", NODES)[0]["id"] == "svc-auth-gateway"
    assert resolve_entity("svc-billing-api", NODES)[0]["name"] == "Billing API"
    assert resolve_entity("BILLING API", NODES)[0]["name"] == "Billing API"
    selected, suggestions = resolve_entity("Gateway", NODES)
    assert selected is None
    assert {s["name"] for s in suggestions} == {"Auth Gateway", "Login Gateway"}
    selected, suggestions = resolve_entity("Biling API", NODES)
    assert selected is None and suggestions[0]["name"] == "Billing API"
    assert resolve_entity("zzzzzzzzzzzzzzzzzz", NODES) == (None, [])


def test_bad_or_missing_citations_fail_closed():
    class Missing:
        def read(self, *args):
            return []
    with pytest.raises(DomainError, match="supporting claim is missing"):
        verified_citations(Missing(), {"claim-unknown"}, [])
