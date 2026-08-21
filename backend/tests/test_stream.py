from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
import pytest
import json

from app import graph
from app.main import app


def post_agent_message(client: TestClient, message: str, state: dict | None = None, run_id: str = "test-run", thread_id: str = "test-thread"):
    return client.post(
        "/api/agent",
        json={
            "thread_id": thread_id,
            "run_id": run_id,
            "state": state or {},
            "messages": [{"id": f"{run_id}-message", "role": "user", "content": message}],
            "tools": [],
            "context": [],
            "forwarded_props": {},
        },
        headers={"Accept": "text/event-stream"},
    )


def latest_state_snapshot(stream: str) -> dict:
    snapshots = []
    for line in stream.splitlines():
        if not line.startswith("data: "):
            continue
        event = json.loads(line.removeprefix("data: "))
        if event.get("type") == "STATE_SNAPSHOT":
            snapshots.append(event["snapshot"])
    assert snapshots
    return snapshots[-1]


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

    response = post_agent_message(TestClient(app), "Create a facility", thread_id="single-turn-thread")

    assert response.status_code == 200
    assert "STATE_SNAPSHOT" in response.text
    assert "Created Facility, Well" in response.text
    assert "facility" in response.text
    assert fake_model.calls == 2


def test_conversation_turns_create_graph(monkeypatch) -> None:
    class FakeModel:
        def bind_tools(self, tools):
            return self

        async def ainvoke(self, messages, config=None):
            if messages[-1].type == "tool":
                return AIMessage(content="Updated the graph.")
            prompt = messages[-1].content.lower()
            if "facility contains well" in prompt:
                return AIMessage(
                    content="",
                    tool_calls=[{"id": "call-relationship", "name": "create_relationship", "args": {"source": "facility", "predicate": "contains", "target": "well"}}],
                )
            if "well" in prompt:
                return AIMessage(content="", tool_calls=[{"id": "call-well", "name": "create_entity", "args": {"name": "Well", "kind": "entity"}}])
            return AIMessage(content="", tool_calls=[{"id": "call-facility", "name": "create_entity", "args": {"name": "Facility", "kind": "entity"}}])

    monkeypatch.setattr(graph, "configured_model", lambda: FakeModel())
    client = TestClient(app)

    facility_response = post_agent_message(client, "Create Facility", run_id="turn-1", thread_id="conversation-thread")
    state = latest_state_snapshot(facility_response.text)
    assert [node["id"] for node in state["nodes"]] == ["facility"]

    well_response = post_agent_message(client, "Create Well", state=state, run_id="turn-2", thread_id="conversation-thread")
    state = latest_state_snapshot(well_response.text)
    assert {node["id"] for node in state["nodes"]} == {"facility", "well"}

    relationship_response = post_agent_message(client, "Facility contains Well", state=state, run_id="turn-3", thread_id="conversation-thread")
    state = latest_state_snapshot(relationship_response.text)
    assert [{"source": edge["source"], "target": edge["target"], "label": edge["label"]} for edge in state["edges"]] == [
        {"source": "facility", "target": "well", "label": "contains"}
    ]


def test_missing_model_configuration_fails_loudly(monkeypatch) -> None:
    for name in ("OPENAI_ENDPOINT", "OPENAI_API_KEY", "OPENAI_DEPLOYMENT"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_ENDPOINT"):
        graph.configured_model()
