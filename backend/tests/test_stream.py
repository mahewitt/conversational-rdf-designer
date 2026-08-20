from fastapi.testclient import TestClient

from app.main import app


def test_agent_stream_returns_shared_graph_event() -> None:
    response = TestClient(app).post("/api/agent/stream", json={"message": "Create a facility"})

    assert response.status_code == 200
    assert "event: assistant_message" in response.text
    assert "event: state_update" in response.text
    assert '"Facility"' in response.text
