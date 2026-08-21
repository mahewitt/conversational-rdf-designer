from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
import pytest

from app import graph
from app.main import app


def test_agent_stream_returns_shared_graph_event(monkeypatch) -> None:
    class FakeModel:
        def __init__(self):
            self.calls = 0

        def bind_tools(self, tools):
            return self

        async def ainvoke(self, messages, config=None):
            self.calls += 1
            if self.calls == 1:
                return AIMessage(
                    content="",
                    tool_calls=[
                        {"id": "call-1", "name": "create_entity", "args": {"name": "Facility", "kind": "entity"}},
                        {"id": "call-2", "name": "create_entity", "args": {"name": "Well", "kind": "entity"}},
                        {
                            "id": "call-3",
                            "name": "create_relationship",
                            "args": {"source": "facility", "predicate": "contains", "target": "well"},
                        },
                    ],
                )
            return AIMessage(content="Created Facility, Well, and a contains relationship.")

    fake_model = FakeModel()
    monkeypatch.setattr(graph, "configured_model", lambda: fake_model)

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
    assert "Created Facility, Well" in response.text
    assert "facility" in response.text
    assert fake_model.calls == 2


def test_missing_model_configuration_fails_loudly(monkeypatch) -> None:
    for name in ("OPENAI_ENDPOINT", "OPENAI_API_KEY", "OPENAI_DEPLOYMENT"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_ENDPOINT"):
        graph.configured_model()
