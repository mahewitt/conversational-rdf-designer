"""LangChain-compatible semantic modelling tools backed by GraphStore."""

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from .graph_store import GraphStore


class CreateEntityInput(BaseModel):
    name: str = Field(description="Singular business name for the entity, for example 'Facility' or 'Data Product'.")
    kind: str = Field(default="entity", description="Entity category. Use 'measurement' only for measurement concepts; otherwise use 'entity'.")


class CreateRelationshipInput(BaseModel):
    source: str = Field(description="Existing source entity ID, for example 'facility'. Create the entity first if it does not exist.")
    predicate: str = Field(description="Relationship phrase, for example 'contains', 'produces', or 'is stored in'.")
    target: str = Field(description="Existing target entity ID, for example 'well'. Create the entity first if it does not exist.")


class AddPropertyInput(BaseModel):
    entity_id: str = Field(description="Existing entity ID to update.")
    property_name: str = Field(description="Property or attribute name to add to the entity.")
    value: Any = Field(default=None, description="Optional property value. Use null when only the attribute name is known.")


class UpdateEntityInput(BaseModel):
    entity_id: str = Field(description="Existing entity ID to update.")
    name: str | None = Field(default=None, description="New display label for the entity.")


class DeleteEntityInput(BaseModel):
    entity_id: str = Field(description="Existing entity ID to delete. Connected relationships are removed automatically.")


class ExtractedEntity(BaseModel):
    name: str = Field(description="Singular entity name extracted from text.")
    kind: str = Field(default="entity", description="Entity category. Use 'measurement' for measurement concepts; otherwise use 'entity'.")


class ExtractedRelationship(BaseModel):
    source: str = Field(description="Source entity name from the extracted entity set.")
    predicate: str = Field(description="Relationship phrase extracted from the text.")
    target: str = Field(description="Target entity name from the extracted entity set.")


class ExtractedAttribute(BaseModel):
    entity: str = Field(description="Entity name from the extracted entity set.")
    property: str = Field(description="Attribute or property name.")
    value: Any = Field(default=None, description="Optional value for the attribute, or null if none is known.")


class ApplyGraphOperationsInput(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list, description="All entities required by this update. Include every endpoint used by relationships.")
    relationships: list[ExtractedRelationship] = Field(default_factory=list, description="Relationships to create after all entities have been created.")
    attributes: list[ExtractedAttribute] = Field(default_factory=list, description="Attributes to add after entities and relationships have been created.")


def create_entity_tool(store: GraphStore) -> StructuredTool:
    def create_entity(name: str, kind: str = "entity") -> dict[str, Any]:
        return store.create_entity(name, kind)

    return StructuredTool.from_function(
        create_entity,
        name="create_entity",
        description="Create one entity node. Use for simple single-entity requests. Prefer singular names. The backend derives the lowercase hyphenated ID.",
        args_schema=CreateEntityInput,
    )


def create_relationship_tool(store: GraphStore) -> StructuredTool:
    def create_relationship(source: str, predicate: str, target: str) -> dict[str, Any]:
        return store.create_relationship(source, predicate, target)

    return StructuredTool.from_function(
        create_relationship,
        name="create_relationship",
        description="Create one relationship between two existing entities. Use existing entity IDs. If endpoints may not exist yet, call create_entity first or use apply_graph_operations.",
        args_schema=CreateRelationshipInput,
    )


def add_property_tool(store: GraphStore) -> StructuredTool:
    def add_property(entity_id: str, property_name: str, value: Any = None) -> dict[str, Any]:
        return store.add_property(entity_id, property_name, value)

    return StructuredTool.from_function(
        add_property,
        name="add_property",
        description="Add or replace one property on an existing entity. Use null for value when the text names an attribute but no value.",
        args_schema=AddPropertyInput,
    )


def update_entity_tool(store: GraphStore) -> StructuredTool:
    def update_entity(entity_id: str, name: str | None = None) -> dict[str, Any]:
        return store.update_entity(entity_id, name)

    return StructuredTool.from_function(
        update_entity,
        name="update_entity",
        description="Rename or update one existing entity. Use this for refinement requests such as 'Rename Well to Production Well'.",
        args_schema=UpdateEntityInput,
    )


def delete_entity_tool(store: GraphStore) -> StructuredTool:
    def delete_entity(entity_id: str) -> dict[str, str]:
        store.delete_entity(entity_id)
        return {"deleted": entity_id}

    return StructuredTool.from_function(
        delete_entity,
        name="delete_entity",
        description="Delete one existing entity and automatically remove its connected relationships.",
        args_schema=DeleteEntityInput,
    )


def apply_graph_operations_tool(store: GraphStore) -> StructuredTool:
    def normalize(items: list[Any] | None) -> list[dict[str, Any]]:
        return [item.model_dump() if isinstance(item, BaseModel) else item for item in items or []]

    def apply_graph_operations(
        entities: list[dict[str, Any]] | None = None,
        relationships: list[dict[str, str]] | None = None,
        attributes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return store.apply_graph_operations(normalize(entities), normalize(relationships), normalize(attributes))

    return StructuredTool.from_function(
        apply_graph_operations,
        name="apply_graph_operations",
        description=(
            "Apply a complete graph update in dependency-safe order. Use this for document extraction, pasted text, "
            "or any request containing multiple facts. Include every entity referenced by every relationship in entities. "
            "The backend creates entities first, then relationships, then attributes, so relationship ordering cannot fail. "
            "Prefer singular entity names such as 'Well' instead of 'Wells'."
        ),
        args_schema=ApplyGraphOperationsInput,
    )


def modelling_tools(store: GraphStore) -> list[StructuredTool]:
    return [
        create_entity_tool(store),
        create_relationship_tool(store),
        add_property_tool(store),
        update_entity_tool(store),
        delete_entity_tool(store),
        apply_graph_operations_tool(store),
    ]
