"""Deterministic LangGraph model used by the hour-one AG-UI endpoint."""

from typing import Annotated, Any, TypedDict

from ag_ui_langgraph.types import CustomEventNames
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class GraphState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    rdf: str


INITIAL_NODES = [
    {"id": "facility", "type": "default", "position": {"x": 120, "y": 150}, "data": {"label": "Facility", "kind": "entity"}},
    {"id": "well", "type": "default", "position": {"x": 430, "y": 280}, "data": {"label": "Well", "kind": "entity"}},
]
INITIAL_EDGES = [{"id": "facility-contains-well", "source": "facility", "target": "well", "label": "contains"}]


def turtle(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    lines = ["@prefix vg: <http://example.com/vibegraph#> .", ""]
    for node in nodes:
        identifier = node["id"].replace("-", "_")
        kind = node.get("data", {}).get("kind", "entity").title()
        lines.append(f"vg:{identifier} a vg:{kind} .")
    lines.append("")
    for edge in edges:
        predicate = edge["label"].replace(" ", "_")
        lines.append(f"vg:{edge['source']} vg:{predicate} vg:{edge['target']} .")
    return "\n".join(lines) + "\n"


def graph_from_state(state: GraphState) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return list(state.get("nodes", INITIAL_NODES)), list(state.get("edges", INITIAL_EDGES))


async def model_turn(state: GraphState, config: RunnableConfig) -> GraphState:
    nodes, edges = graph_from_state(state)
    latest = state.get("messages", [])[-1] if state.get("messages") else None
    prompt = str(getattr(latest, "content", latest or "")).lower()

    def add_node(node_id: str, label: str, kind: str, x: int, y: int) -> None:
        if not any(node["id"] == node_id for node in nodes):
            nodes.append({"id": node_id, "type": "default", "position": {"x": x, "y": y}, "data": {"label": label, "kind": kind}})

    if "facility" in prompt:
        add_node("facility", "Facility", "entity", 120, 150)
    if "well" in prompt:
        add_node("well", "Well", "entity", 430, 280)
    if "measurement" in prompt or "production" in prompt:
        add_node("measurement", "Production Measurement", "measurement", 720, 150)
    ids = {node["id"] for node in nodes}
    if any(word in prompt for word in ("contain", "with", "inside")) and {"facility", "well"} <= ids:
        if not any(edge["source"] == "facility" and edge["target"] == "well" for edge in edges):
            edges.append({"id": "facility-contains-well", "source": "facility", "target": "well", "label": "contains"})
    if {"well", "measurement"} <= ids and not any(edge["source"] == "well" and edge["target"] == "measurement" for edge in edges):
        edges.append({"id": "well-produces-measurement", "source": "well", "target": "measurement", "label": "produces"})

    current = {"nodes": nodes, "edges": edges, "rdf": turtle(nodes, edges)}
    await adispatch_custom_event(CustomEventNames.ManuallyEmitState, current, config=config)
    await adispatch_custom_event(
        CustomEventNames.ManuallyEmitMessage,
        {"message_id": "vibegraph-status", "message": "The shared graph is ready for your next instruction."},
        config=config,
    )
    return {**current, "messages": [AIMessage(content="I'm shaping that into a semantic model.")]}


builder = StateGraph(GraphState)
builder.add_node("model_turn", model_turn)
builder.add_edge(START, "model_turn")
builder.add_edge("model_turn", END)
model_graph = builder.compile(checkpointer=MemorySaver())
