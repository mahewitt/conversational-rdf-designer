"""LangGraph agent used by the VibeGraph AG-UI endpoint."""

from typing import Annotated, Any, TypedDict

from ag_ui_langgraph.types import CustomEventNames
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from .graph_store import GraphStore
from .semantic_tools import modelling_tools

load_dotenv()


class GraphState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    rdf: str
    namespace: dict[str, str]


INITIAL_NODES: list[dict[str, Any]] = []
INITIAL_EDGES: list[dict[str, Any]] = []
DEFAULT_NAMESPACE = {"prefix": "vg", "namespace": "http://example.com/vibegraph#"}
SYSTEM_PROMPT = """You are VibeGraph, a semantic modelling assistant. Convert business language and visual diagrams into graph operations.

Tool contract:
- Use create_entity for a simple request that creates one entity.
- Use create_relationship only when both endpoint entities already exist in graph state or were created by an earlier tool call.
- Use add_property for attributes on an existing entity.
- Use update_entity for rename, refinement, or description requests.
- Use delete_entity only when the user clearly asks to remove an entity.
- Use delete_relationship when the user asks to remove, unlink, or negate one relationship without deleting entities.
- Use update_relationship when the user asks to change the predicate or endpoints of an existing relationship.
- Use merge_entities when the user says two entities are duplicates or should be the same thing.
- Use list_graph before edits when the existing entities or relationships are unclear.
- Use clear_graph when the user asks to delete all entities, clear the graph, reset the model, remove everything, or start over. Do not ask for confirmation yourself; the clear_graph tool requests human approval.
- Use set_namespace when the user asks to change the OWL/Turtle prefix, namespace, base IRI, or entity IRI namespace.
- Use save_model when the user asks to save the model, persist the graph, save as RDF, export RDF, or download the Turtle file.
- Use apply_graph_operations for pasted documents, extraction requests, ER/UML/schema diagrams, image inputs, or any request with multiple facts, entities, relationships, or attributes.

Diagram and ER extraction rules:
- When an image or diagram (such as an ER diagram, UML class diagram, database schema, or conceptual model) is provided:
  1. Identify all entity types / tables / classes (typically shown as boxes or rectangles). Use singular names (e.g., 'Customer', 'Order', 'Policy').
  2. Identify all attributes / fields / properties for each entity (shown in list boxes, tables, or connected ovals). Include data types or values if visible.
  3. Identify all relationships, associations, or foreign keys connecting entities (shown as lines, diamonds, arrows, or crow's feet). Convert these into active predicate phrases (e.g. 'places', 'contains', 'has', 'belongs to').
  4. Infer concise, domain-specific descriptions for entities from their labels and diagram context.
  5. Call `apply_graph_operations` with all extracted entities, relationships, and attributes in a single dependency-safe update.

Extraction rules:
- For apply_graph_operations, include every entity referenced by every relationship in the entities list.
- Include a concise, domain-specific description for each entity when it can be inferred from the user request or source text/diagram.
- Prefer singular entity names: Well, Hydrocarbon, Sensor, Data Product.
- Create entities before relationships by using apply_graph_operations rather than many separate relationship calls.

Keep responses concise and explain what changed. If the request is not a modelling request, say what you can model."""


def owl_turtle(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], namespace_config: dict[str, str] | None = None) -> str:
    namespace_config = namespace_config or DEFAULT_NAMESPACE
    prefix = namespace_config.get("prefix") or DEFAULT_NAMESPACE["prefix"]
    namespace = namespace_config.get("namespace") or DEFAULT_NAMESPACE["namespace"]
    lines = [
        f"@prefix {prefix}: <{namespace}> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        f"<{namespace}> a owl:Ontology .",
        "",
    ]
    for node in nodes:
        identifier = node["id"].replace("-", "_")
        label = node.get("data", {}).get("label", node["id"])
        description = node.get("data", {}).get("description") or f"A {label} in this semantic model."
        lines.append(f'{prefix}:{identifier} a owl:Class ;')
        lines.append(f'    rdfs:label "{turtle_literal(label)}" ;')
        lines.append(f'    rdfs:comment "{turtle_literal(description)}" .')
    lines.append("")
    for edge in edges:
        predicate = edge["label"].replace(" ", "_")
        source = edge["source"].replace("-", "_")
        target = edge["target"].replace("-", "_")
        lines.append(f"{prefix}:{predicate} a owl:ObjectProperty ;")
        lines.append(f"    rdfs:domain {prefix}:{source} ;")
        lines.append(f"    rdfs:range {prefix}:{target} .")
    return "\n".join(lines) + "\n"


def turtle_literal(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def turtle(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    return owl_turtle(nodes, edges)


def graph_from_state(state: GraphState) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return list(state.get("nodes", INITIAL_NODES)), list(state.get("edges", INITIAL_EDGES))


def namespace_from_state(state: GraphState) -> dict[str, str]:
    return dict(state.get("namespace", DEFAULT_NAMESPACE))


def configured_model():
    """Build the configured OpenAI-compatible chat model lazily."""
    import os

    endpoint = os.getenv("OPENAI_ENDPOINT")
    api_key = os.getenv("OPENAI_API_KEY")
    deployment = os.getenv("OPENAI_DEPLOYMENT")
    if not endpoint or not api_key or not deployment:
        raise RuntimeError("OPENAI_ENDPOINT, OPENAI_API_KEY, and OPENAI_DEPLOYMENT must be configured")
    return init_chat_model(
        model=deployment,
        model_provider="openai",
        api_key=api_key,
        base_url=endpoint,
        temperature=0,
    )


async def call_model(state: GraphState, config: RunnableConfig) -> GraphState:
    nodes, edges = graph_from_state(state)
    store = GraphStore(nodes, edges, namespace_from_state(state))
    tools = {tool.name: tool for tool in modelling_tools(store)}

    try:
        response = await model_response(state, tools, config)
    except Exception as exc:
        return {"messages": [AIMessage(content=f"Agent run failed: {exc}")]}
    if not isinstance(response, AIMessage):
        response = AIMessage(content="Agent run failed: the model did not return an assistant message.")
    return {"messages": [response]}


async def model_response(state: GraphState, tools: dict[str, Any], config: RunnableConfig) -> AIMessage | None:
    model = configured_model()
    bound_model = model.bind_tools(list(tools.values()))
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state.get("messages", [])]
    response = await bound_model.ainvoke(messages, config=config)
    return response if isinstance(response, AIMessage) else None


def run_tools(state: GraphState) -> GraphState:
    nodes, edges = graph_from_state(state)
    store = GraphStore(nodes, edges, namespace_from_state(state))
    tools = {tool.name: tool for tool in modelling_tools(store)}
    latest = state.get("messages", [])[-1] if state.get("messages") else None
    if not isinstance(latest, AIMessage) or not latest.tool_calls:
        return {}

    tool_messages = []
    for call in latest.tool_calls:
        selected_tool = tools.get(call["name"])
        if selected_tool is None:
            tool_messages.append(ToolMessage(content=f"Unknown tool: {call['name']}", tool_call_id=call["id"]))
            continue
        try:
            result = selected_tool.invoke(call["args"])
        except GraphInterrupt:
            raise
        except Exception as exc:
            result = {"error": str(exc)}
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    return {**store.to_state(), "rdf": owl_turtle(store.nodes, store.edges, store.namespace), "messages": tool_messages}


async def emit_state(state: GraphState, config: RunnableConfig) -> GraphState:
    nodes, edges = graph_from_state(state)
    namespace = namespace_from_state(state)
    current = {"nodes": nodes, "edges": edges, "namespace": namespace, "rdf": owl_turtle(nodes, edges, namespace)}
    await adispatch_custom_event(CustomEventNames.ManuallyEmitState, current, config=config)
    return current


def route_after_model(state: GraphState) -> str:
    latest = state.get("messages", [])[-1] if state.get("messages") else None
    if isinstance(latest, AIMessage) and latest.tool_calls:
        return "run_tools"
    return "emit_state"


builder = StateGraph(GraphState)
builder.add_node("call_model", call_model)
builder.add_node("run_tools", run_tools)
builder.add_node("emit_state", emit_state)
builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", route_after_model, {"run_tools": "run_tools", "emit_state": "emit_state"})
builder.add_edge("run_tools", "call_model")
builder.add_edge("emit_state", END)
model_graph = builder.compile(checkpointer=MemorySaver())
