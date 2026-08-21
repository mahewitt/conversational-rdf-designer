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


def test_document_extraction_uses_bulk_graph_operations(monkeypatch) -> None:
    class FakeModel:
        def bind_tools(self, tools):
            return self

        async def ainvoke(self, messages, config=None):
            if messages[-1].type == "tool":
                return AIMessage(content="Entities and relationships have been extracted and created.")
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-extract",
                        "name": "apply_graph_operations",
                        "args": {
                            "entities": [
                                {"name": "Facility"},
                                {"name": "Well"},
                                {"name": "Hydrocarbon"},
                                {"name": "Sensor"},
                                {"name": "Production"},
                                {"name": "Data Product"},
                            ],
                            "relationships": [
                                {"source": "Facility", "predicate": "contains", "target": "Well"},
                                {"source": "Well", "predicate": "produces", "target": "Hydrocarbon"},
                                {"source": "Sensor", "predicate": "measures", "target": "Production"},
                                {"source": "Production", "predicate": "is stored in", "target": "Data Product"},
                            ],
                        },
                    }
                ],
            )

    monkeypatch.setattr(graph, "configured_model", lambda: FakeModel())
    response = post_agent_message(
        TestClient(app),
        "Extract entities and relationships:\n\nA facility contains multiple wells.\nWells produce hydrocarbons.\nSensors measure production.\nProduction data is stored in a data product.",
        run_id="extract-turn",
        thread_id="extract-thread",
    )
    state = latest_state_snapshot(response.text)

    assert {node["id"] for node in state["nodes"]} == {"facility", "well", "hydrocarbon", "sensor", "production", "data-product"}
    assert {edge["label"] for edge in state["edges"]} == {"contains", "produces", "measures", "is stored in"}


def test_clear_graph_tool_removes_all_graph_state(monkeypatch) -> None:
    from app import semantic_tools
    interrupt_payloads = []

    class FakeModel:
        def bind_tools(self, tools):
            return self

        async def ainvoke(self, messages, config=None):
            if messages[-1].type == "tool":
                return AIMessage(content="Cleared the graph.")
            return AIMessage(content="", tool_calls=[{"id": "call-clear", "name": "clear_graph", "args": {"reason": "The user asked to delete all entities."}}])

    def approve_interrupt(value):
        interrupt_payloads.append(value)
        return {"approved": True}

    monkeypatch.setattr(semantic_tools, "interrupt", approve_interrupt)
    monkeypatch.setattr(graph, "configured_model", lambda: FakeModel())
    response = post_agent_message(
        TestClient(app),
        "Delete all entities",
        state={
            "nodes": [
                {"id": "facility", "type": "default", "position": {"x": 0, "y": 0}, "data": {"label": "Facility", "kind": "entity"}},
                {"id": "well", "type": "default", "position": {"x": 100, "y": 0}, "data": {"label": "Well", "kind": "entity"}},
            ],
            "edges": [{"id": "facility-contains-well", "source": "facility", "target": "well", "label": "contains"}],
            "rdf": "existing",
        },
        run_id="clear-turn",
        thread_id="clear-thread",
    )
    state = latest_state_snapshot(response.text)

    assert state["nodes"] == []
    assert state["edges"] == []
    assert state["rdf"] == "@prefix vg: <http://example.com/vibegraph#> .\n\n\n"
    assert interrupt_payloads[0]["reason"] == "clear_graph_confirmation"


def test_delete_relationship_tool_removes_edge_only(monkeypatch) -> None:
    class FakeModel:
        def bind_tools(self, tools):
            return self

        async def ainvoke(self, messages, config=None):
            if messages[-1].type == "tool":
                return AIMessage(content="Removed the contains relationship.")
            return AIMessage(
                content="",
                tool_calls=[
                    {"id": "call-delete-relationship", "name": "delete_relationship", "args": {"source": "facility", "predicate": "contains", "target": "well"}}
                ],
            )

    monkeypatch.setattr(graph, "configured_model", lambda: FakeModel())
    response = post_agent_message(
        TestClient(app),
        "Facility should not contain Well",
        state={
            "nodes": [
                {"id": "facility", "type": "default", "position": {"x": 0, "y": 0}, "data": {"label": "Facility", "kind": "entity"}},
                {"id": "well", "type": "default", "position": {"x": 100, "y": 0}, "data": {"label": "Well", "kind": "entity"}},
            ],
            "edges": [{"id": "facility-contains-well", "source": "facility", "target": "well", "label": "contains"}],
            "rdf": "existing",
        },
        run_id="delete-relationship-turn",
        thread_id="delete-relationship-thread",
    )
    state = latest_state_snapshot(response.text)

    assert {node["id"] for node in state["nodes"]} == {"facility", "well"}
    assert state["edges"] == []


def test_merge_entities_tool_rewires_graph_state(monkeypatch) -> None:
    class FakeModel:
        def bind_tools(self, tools):
            return self

        async def ainvoke(self, messages, config=None):
            if messages[-1].type == "tool":
                return AIMessage(content="Merged duplicate production entities.")
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-merge",
                        "name": "merge_entities",
                        "args": {"source_entity_id": "production", "target_entity_id": "production-data", "merged_name": "Production Data"},
                    }
                ],
            )

    monkeypatch.setattr(graph, "configured_model", lambda: FakeModel())
    response = post_agent_message(
        TestClient(app),
        "Production and Production Data are the same thing",
        state={
            "nodes": [
                {"id": "production", "type": "default", "position": {"x": 0, "y": 0}, "data": {"label": "Production", "kind": "entity"}},
                {"id": "production-data", "type": "default", "position": {"x": 100, "y": 0}, "data": {"label": "Production Data", "kind": "entity"}},
                {"id": "data-product", "type": "default", "position": {"x": 200, "y": 0}, "data": {"label": "Data Product", "kind": "entity"}},
            ],
            "edges": [
                {"id": "production-stored", "source": "production", "target": "data-product", "label": "is stored in"},
                {"id": "production-data-stored", "source": "production-data", "target": "data-product", "label": "is stored in"},
            ],
            "rdf": "existing",
        },
        run_id="merge-turn",
        thread_id="merge-thread",
    )
    state = latest_state_snapshot(response.text)

    assert {node["id"] for node in state["nodes"]} == {"production-data", "data-product"}
    assert [{"source": edge["source"], "label": edge["label"], "target": edge["target"]} for edge in state["edges"]] == [
        {"source": "production-data", "label": "is stored in", "target": "data-product"}
    ]


def test_missing_model_configuration_fails_loudly(monkeypatch) -> None:
    for name in ("OPENAI_ENDPOINT", "OPENAI_API_KEY", "OPENAI_DEPLOYMENT"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_ENDPOINT"):
        graph.configured_model()
