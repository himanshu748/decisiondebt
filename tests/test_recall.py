import json
from backend.app.settings import ROOT
from backend.app.ingest.entities import Catalog
from backend.app.ingest.parsers import load_directory
from backend.app.ingest.extract import extract


def test_precision_recall():
    catalog = Catalog()
    sources = load_directory(ROOT / "data/synthetic/raw", ROOT / "data/synthetic/raw")
    actual = {
        (c.relation, c.subject_id, c.object_id)
        for s in sources
        for c in extract(s, catalog)
        if c.status == "verified"
    }
    expected = {
        tuple(t)
        for t in json.loads((ROOT / "tests/fixtures/oracle_expected.json").read_text())[
            "relations"
        ]
    }
    tp = len(actual & expected)
    precision = tp / len(actual)
    recall = tp / len(expected)
    report = dict(
        expected=len(expected),
        actual=len(actual),
        true_positives=tp,
        precision=precision,
        recall=recall,
        false_positives=sorted(actual - expected),
        false_negatives=sorted(expected - actual),
    )
    (ROOT / "evidence/test-results/precision-recall.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    assert precision == 1, report
    assert recall >= 0.95, report
