"""LangChain-compatible semantic modelling tools backed by GraphStore."""

from typing import Any

from langchain_core.tools import StructuredTool

from .graph_store import GraphStore


def create_entity_tool(store: GraphStore) -> StructuredTool:
    def create_entity(name: str, kind: str = "entity") -> dict[str, Any]:
        return store.create_entity(name, kind)

    return StructuredTool.from_function(
        create_entity,
        name="create_entity",
        description="Create an entity node in the semantic graph.",
    )


def create_relationship_tool(store: GraphStore) -> StructuredTool:
    def create_relationship(source: str, predicate: str, target: str) -> dict[str, Any]:
        return store.create_relationship(source, predicate, target)

    return StructuredTool.from_function(
        create_relationship,
        name="create_relationship",
        description="Create a relationship between two existing entities.",
    )


def add_property_tool(store: GraphStore) -> StructuredTool:
    def add_property(entity_id: str, property_name: str, value: Any = None) -> dict[str, Any]:
        return store.add_property(entity_id, property_name, value)

    return StructuredTool.from_function(
        add_property,
        name="add_property",
        description="Add or replace a property on an entity.",
    )


def update_entity_tool(store: GraphStore) -> StructuredTool:
    def update_entity(entity_id: str, name: str | None = None) -> dict[str, Any]:
        return store.update_entity(entity_id, name)

    return StructuredTool.from_function(
        update_entity,
        name="update_entity",
        description="Update an entity label.",
    )


def delete_entity_tool(store: GraphStore) -> StructuredTool:
    def delete_entity(entity_id: str) -> dict[str, str]:
        store.delete_entity(entity_id)
        return {"deleted": entity_id}

    return StructuredTool.from_function(
        delete_entity,
        name="delete_entity",
        description="Delete an entity and its relationships.",
    )


def modelling_tools(store: GraphStore) -> list[StructuredTool]:
    return [
        create_entity_tool(store),
        create_relationship_tool(store),
        add_property_tool(store),
        update_entity_tool(store),
        delete_entity_tool(store),
    ]
