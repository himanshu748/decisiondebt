import pytest
from backend.app.settings import ROOT
from backend.app.graph.client import Graph
from backend.app.graph.schema import initialize
from backend.app.ingest.entities import Catalog
from backend.app.ingest.parsers import load_directory
from backend.app.ingest.refresh import refresh


@pytest.fixture(scope="module")
def graph():
    g = Graph("decisiondebt_test")
    g.write("MATCH (n) DETACH DELETE n")
    catalog = Catalog()
    initialize(g, catalog)
    refresh(
        g,
        load_directory(ROOT / "data/synthetic/raw", ROOT / "data/synthetic/raw"),
        catalog,
    )
    return g
