import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.settings import ROOT
from backend.app.graph.client import Graph
from backend.app.graph.schema import initialize
from backend.app.ingest.entities import Catalog
from backend.app.ingest.parsers import load_directory
from backend.app.ingest.refresh import refresh

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=ROOT / "data/synthetic/raw")
    p.add_argument("--reset", action="store_true")
    a = p.parse_args()
    g = Graph()
    catalog = Catalog()
    if a.reset:
        g.write("MATCH (n) DETACH DELETE n")
    initialize(g, catalog)
    report = refresh(g, load_directory(a.dir, ROOT / "data/synthetic/raw"), catalog)
    print(json.dumps(report, indent=2))
