import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, graph
from backend.app.graph.client import GraphUnavailable
from backend.app.settings import settings


@pytest.mark.parametrize("mode", ["public-readonly", "local-admin"])
def test_shell_survives_graph_outage_and_declares_its_mode(monkeypatch, mode):
    monkeypatch.setattr(settings, "mode", mode)

    def unavailable():
        raise GraphUnavailable()

    app.dependency_overrides[graph] = unavailable
    try:
        with TestClient(app) as client:
            response = client.get("/studio?tab=Action%20Board")
            assert response.status_code == 200
            assert response.headers["cache-control"] == "no-store"
            assert f'name="decisiondebt-mode" content="{mode}"' in response.text
            assert "Retry loading" in response.text
            assert "https://youtu.be/_a0vrYwOlME" in response.text
    finally:
        app.dependency_overrides.pop(graph, None)
