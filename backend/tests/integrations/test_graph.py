import json
from backend.app.settings import ROOT
from backend.app.domain.impact import preview
from backend.app.domain.company import summary
from backend.app.domain.evidence import claim_evidence, search
from backend.app.ingest.parsers import parse
from backend.app.ingest.entities import Catalog
from backend.app.ingest.refresh import refresh
import importlib.util

spec = importlib.util.spec_from_file_location(
    "independent_oracle", ROOT / "tests/oracle.py"
)
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def test_live_counts(graph):
    s = summary(graph)
    assert s["counts"]["service"] == 60
    assert s["counts"]["source"] == 94
    assert s["counts"]["semantic_edges"] >= 100


def test_blast_radius_and_oracle(graph):
    p = preview(graph, "dec-auth-002")
    truth = json.loads((ROOT / "tests/fixtures/oracle_expected.json").read_text())
    expected = oracle.bfs(truth["relations"], truth["canonical"]["root"])
    assert {i["service_id"]: i["depth"] for i in p["impacts"]} == expected
    assert (
        p["counts"]["services"] == len(p["impacts"])
        and p["max_hops"] == 5
        and p["truncated"]
    )
    assert p["truncation_examples"] == [
        {"service_id": "svc-directory-sync", "name": "Directory Sync", "depth": 6}
    ]
    assert "svc-directory-sync" not in expected


def test_diamond_cycle_owners(graph):
    p = preview(graph, "dec-auth-002")
    items = {i["service_id"]: i for i in p["impacts"]}
    assert (
        items["svc-session-broker"]["depth"] == 2
        and items["svc-session-broker"]["alternative_path_count"] == 2
    )
    assert len(items) == len(p["impacts"])
    assert items["svc-token-cache"]["owner_status"] == "unowned"
    assert (
        items["svc-session-broker"]["owner_status"] == "conflict"
        and len(items["svc-session-broker"]["owner_ids"]) == 2
    )
    assert p["elapsed_ms"] < 3000
    for i in p["impacts"]:
        for path, claims in zip(i["paths"], i["path_claim_ids"]):
            assert len(path) - 1 == len(claims)


def test_truncation_example_disappears_when_already_in_scope(graph):
    ident = "ticket-frontier-shortcut"
    try:
        refresh(
            graph,
            [make("Directory Sync depends on Auth Gateway for identity.", ident)],
            Catalog(),
        )
        result = preview(graph, "dec-auth-002")
        assert any(
            item["service_id"] == "svc-directory-sync" and item["depth"] == 1
            for item in result["impacts"]
        )
        assert result["cycle_detected"]
        assert not result["truncated"]
        assert result["truncation_examples"] == []
    finally:
        refresh(graph, [make("The review is still open.", ident)], Catalog())


def test_preview_readonly(graph):
    before = graph.revision()
    states = graph.read(
        "MATCH (d:Decision) RETURN d.id AS id,d.status AS status ORDER BY id"
    )
    for _ in range(3):
        assert preview(graph, "dec-auth-002")["decision_status"] == "proposed"
    assert (
        graph.revision() == before
        and graph.read(
            "MATCH (d:Decision) RETURN d.id AS id,d.status AS status ORDER BY id"
        )
        == states
    )
    assert graph.read("MATCH ()-[r:SUPERSEDES]->() RETURN count(r) AS n")[0]["n"] == 0


def test_drift_tiers(graph):
    p = preview(graph, "dec-auth-002")
    ds = p["drifts"]
    assert {d["tier"] for d in ds} == {1, 2, 3}
    assert {d["certainty"] for d in ds} == {
        "confirmed_reference_obsolete",
        "suspected_drift",
        "needs_review",
    }
    assert all(d["source_id"] != "doc-001" for d in ds if d["tier"] == 2)
    assert {d["source_id"] for d in ds if d["tier"] == 3} == {
        "doc-001",
        "doc-002",
        "doc-004",
    }
    assert any(
        q["query_id"] == "Q7" and "fulltext.queryNodes" in q["cypher"]
        for q in p["query_trace"]
    )
    assert search(graph, "OrionAuth") and not search(graph, "OrionAuthentication")
    by_id = search(graph, "svc-token-cache", kind="chat")
    assert by_id and all(row["excerpt"].casefold() == "token cache" for row in by_id)
    assert all("Finley Rao" not in row["context"] for row in by_id)
    assert search(graph, "unrecognized-hyphenated-alias") == []


def test_every_active_edge_anchored(graph):
    rows = graph.read(
        "MATCH ()-[r]->() WHERE r.claim_id IS NOT NULL RETURN r.claim_id AS claim_id"
    )
    assert len(rows) >= 100
    for r in rows:
        assert claim_evidence(graph, r["claim_id"])["anchor_verified"]


def make(body, ident="ticket-dynamic"):
    return parse(
        "ticket",
        json.dumps(
            dict(
                id=ident,
                title="Synthetic dynamic update",
                author_id="person-007",
                created_at="2026-10-10T10:00:00+05:30",
                body=body,
            )
        ),
    )


def test_source_update_independent_support(graph):
    c = Catalog()
    body = "External Portal depends on Billing API for identity."
    a = make(body)
    b = make(body, "ticket-independent")
    refresh(graph, [a, b], c)
    p = preview(graph, "dec-auth-002")
    assert any(i["service_id"] == "svc-external-portal" for i in p["impacts"])
    rev = graph.revision()
    assert refresh(graph, [a, b], c)["changed"] == 0 and graph.revision() == rev
    refresh(graph, [make("The review is still open.")], c)
    assert any(
        i["service_id"] == "svc-external-portal"
        for i in preview(graph, "dec-auth-002")["impacts"]
    )
    refresh(graph, [make("The review is still open.", "ticket-independent")], c)
    assert not any(
        i["service_id"] == "svc-external-portal"
        for i in preview(graph, "dec-auth-002")["impacts"]
    )
    assert (
        graph.read(
            "MATCH (c:Claim {source_id:'ticket-dynamic',relation:'DEPENDS_ON'}) RETURN c.status AS status"
        )[0]["status"]
        == "retracted"
    )


def test_invalid_review_date_is_unknown_not_overdue(graph):
    raw = "---\nid: doc-unknown-review\ntitle: Synthetic unknown date\nauthor_id: person-001\ncreated_at: 2026-10-10T10:00:00+05:30\nlast_reviewed_at: not-a-date\n---\nThis document describes Login Gateway.\n"
    refresh(graph, [parse("doc", raw)], Catalog())
    result = preview(graph, "dec-auth-002")
    assert any(
        d["source_id"] == "doc-unknown-review" and d["kind"] == "unknown_review_date"
        for d in result["review_date_issues"]
    )
    assert not any(d["source_id"] == "doc-unknown-review" for d in result["drifts"])
    assert result["cycle_detected"] is True
