import hashlib
import json
import re
import pytest
from backend.app.settings import ROOT
from backend.app.ingest.entities import Catalog
from backend.app.ingest.parsers import parse, load_directory
from backend.app.ingest.extract import extract
from backend.app.ingest.verify import verify
from backend.app.domain.rank import rank


def record(body):
    return parse(
        "ticket",
        json.dumps(
            dict(
                id="ticket-test",
                title="Synthetic test",
                author_id="person-001",
                created_at="2026-10-10T10:00:00+05:30",
                body=body,
            )
        ),
    )


def test_fixture_counts():
    c = Catalog()
    sources = load_directory(ROOT / "data/synthetic/raw", ROOT / "data/synthetic/raw")
    assert {
        label: sum(e["label"] == label for e in c.entities)
        for label in ["Service", "Team", "Person", "Project"]
    } == dict(Service=60, Team=8, Person=24, Project=12)
    assert {
        kind: sum(s.kind == kind for s in sources) for kind in ["doc", "ticket", "chat"]
    } == dict(doc=40, ticket=30, chat=24)
    assert all(
        s.sha256 == hashlib.sha256(s.raw_text.encode()).hexdigest() for s in sources
    )


@pytest.mark.parametrize(
    "phrase",
    [
        "Login Gateway depends on Auth Gateway.",
        "Login Gateway calls Auth Gateway.",
        "Login Gateway uses Auth Gateway.",
    ],
)
def test_dependency_patterns(phrase):
    src = record(phrase)
    claims = extract(src, Catalog())
    assert any(c.relation == "DEPENDS_ON" and verify(c, src, Catalog()) for c in claims)


@pytest.mark.parametrize(
    "phrase",
    [
        "I think Login Gateway calls Auth Gateway.",
        "Login Gateway no longer calls Auth Gateway.",
        "Login Gateway maybe uses Auth Gateway.",
        "Avery Chen probably owns Token Cache.",
    ],
)
def test_hedges_and_negation(phrase):
    cs = [c for c in extract(record(phrase), Catalog()) if c.relation != "AUTHORED"]
    assert cs and all(c.status == "candidate" for c in cs)


def test_metadata_anchor():
    s = record("Avery Chen owns Login Gateway.")
    c = next(c for c in extract(s, Catalog()) if c.relation == "AUTHORED")
    assert (
        c.anchor_field == "raw_text"
        and "author_id" in c.excerpt
        and verify(c, s, Catalog())
    )


def test_parser_validation():
    with pytest.raises(ValueError):
        parse("doc", "missing front matter")
    with pytest.raises(ValueError):
        record("x" * 65537)
    with pytest.raises(ValueError):
        parse("csv", "data")


def test_oracle_isolation():
    for base in [ROOT / "backend/app", ROOT / "tools/ingest.py"]:
        paths = base.rglob("*.py") if base.is_dir() else [base]
        for p in paths:
            text = p.read_text()
            assert not re.search(
                r"(?:from|import)\s+tests\b|oracle_expected|relationships\.json", text
            ), p
    catalog = json.loads((ROOT / "data/synthetic/catalog.json").read_text())
    assert all(
        not set(e).intersection(
            {"depends_on", "owner", "edges", "uses", "references", "changes"}
        )
        for e in catalog["entities"]
    )


@pytest.mark.parametrize(
    "depth,criticality,status,tiers,expected",
    [
        (0, 3, "single_primary", set(), 75),
        (3, 2, "unowned", {1, 2, 3}, 64),
        (2, 3, "conflict", set(), 63),
        (5, 1, "single_primary", set(), 15),
    ],
)
def test_ranking(depth, criticality, status, tiers, expected):
    assert rank(depth, criticality, status, tiers)[0] == expected
