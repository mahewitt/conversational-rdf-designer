from fastapi.testclient import TestClient

from app.main import app


def test_agent_stream_returns_shared_graph_event() -> None:
    response = TestClient(app).post(
        "/api/agent",
        json={
            "thread_id": "test-thread",
            "run_id": "test-run",
            "state": {},
            "messages": [{"id": "message-1", "role": "user", "content": "Create a facility"}],
            "tools": [],
            "context": [],
            "forwarded_props": {},
        },
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert "STATE_SNAPSHOT" in response.text
    assert "TEXT_MESSAGE" in response.text
    assert "facility" in response.text
