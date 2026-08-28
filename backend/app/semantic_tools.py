"""LangChain-compatible semantic modelling tools backed by GraphStore."""

from typing import Any

from langchain_core.tools import StructuredTool
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from .graph_store import GraphStore


class CreateEntityInput(BaseModel):
    name: str = Field(description="Singular business name for the entity, for example 'Facility' or 'Data Product'.")
    description: str | None = Field(
        default=None,
        description=(
            "One-sentence, domain-specific definition of what this entity represents in the current model. "
            "State the purpose or role directly (e.g. 'Provides goods or services to other entities in the supply "
            "chain.'); do not start with 'An entity that ...' or 'A {name} that ...'. Always write a specific "
            "definition grounded in the conversation's domain; do not omit this, since the backend's fallback is "
            "generic and low quality."
        ),
    )


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
    description: str | None = Field(
        default=None,
        description=(
            "One-sentence, domain-specific definition of what this entity represents. State the purpose or role "
            "directly; do not start with 'An entity that ...' or similar filler."
        ),
    )


class DeleteEntityInput(BaseModel):
    entity_id: str = Field(description="Existing entity ID to delete. Connected relationships are removed automatically.")


class DeleteRelationshipInput(BaseModel):
    source: str = Field(description="Existing source entity ID, for example 'facility'.")
    predicate: str = Field(description="Relationship phrase to remove, for example 'contains'.")
    target: str = Field(description="Existing target entity ID, for example 'well'.")


class UpdateRelationshipInput(BaseModel):
    source: str = Field(description="Current source entity ID of the relationship to update.")
    predicate: str = Field(description="Current relationship phrase to update.")
    target: str = Field(description="Current target entity ID of the relationship to update.")
    new_predicate: str | None = Field(default=None, description="Replacement relationship phrase, if changing the predicate.")
    new_source: str | None = Field(default=None, description="Replacement source entity ID, if changing the source endpoint.")
    new_target: str | None = Field(default=None, description="Replacement target entity ID, if changing the target endpoint.")


class MergeEntitiesInput(BaseModel):
    source_entity_id: str = Field(description="Entity ID to merge away. Its relationships will be rewired to the target entity.")
    target_entity_id: str = Field(description="Entity ID that remains after the merge.")
    merged_name: str | None = Field(default=None, description="Optional final display label for the surviving target entity.")


class ClearGraphInput(BaseModel):
    reason: str = Field(description="Brief reason the user asked to clear the graph. The tool asks the human for approval before deleting anything.")


class SetNamespaceInput(BaseModel):
    prefix: str = Field(description="Short Turtle prefix to use for generated OWL entities, for example 'prod' or 'oil'. Do not include the trailing colon.")
    namespace: str = Field(description="Base IRI namespace for generated OWL entities, for example 'https://example.com/model/production#'.")


class ExtractedEntity(BaseModel):
    name: str = Field(description="Singular entity name extracted from text.")
    description: str | None = Field(
        default=None,
        description=(
            "One-sentence, domain-specific definition of this entity, grounded in the source text/diagram and its "
            "domain. State the purpose or role directly; do not start with 'An entity that ...' or similar filler. "
            "Always provide this for every extracted entity rather than leaving it blank."
        ),
    )


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


class SaveModelInput(BaseModel):
    name: str | None = Field(default=None, description="Optional name for the saved model (e.g. 'SolarPowerOntology'). If not provided, defaults to 'semantic_model'.")


class SaveSpeckitInput(BaseModel):
    name: str | None = Field(default=None, description="Optional name for the saved spec-kit file (e.g. 'SolarPowerDataProduct'). If not provided, defaults to 'spec'.")


def create_entity_tool(store: GraphStore) -> StructuredTool:
    def create_entity(name: str, description: str | None = None) -> dict[str, Any]:
        return store.create_entity(name, description)

    return StructuredTool.from_function(
        create_entity,
        name="create_entity",
        description="Create one entity node, with an optional concise domain definition. Use for simple single-entity requests. Prefer singular names. The backend derives the lowercase hyphenated ID and generates a generic definition when none is supplied.",
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
    def update_entity(entity_id: str, name: str | None = None, description: str | None = None) -> dict[str, Any]:
        return store.update_entity(entity_id, name, description)

    return StructuredTool.from_function(
        update_entity,
        name="update_entity",
        description="Rename or update one existing entity, including its human-readable definition. Use this for refinement requests such as 'Rename Well to Production Well' or 'Describe Claim as an insurance claim submitted by a policyholder'.",
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


def delete_relationship_tool(store: GraphStore) -> StructuredTool:
    def delete_relationship(source: str, predicate: str, target: str) -> dict[str, int]:
        return store.delete_relationship(source, predicate, target)

    return StructuredTool.from_function(
        delete_relationship,
        name="delete_relationship",
        description="Delete one relationship without deleting either entity. Use when the user asks to remove, unlink, or negate a specific relationship such as 'Facility should not contain Well'. Returns the number of deleted relationships.",
        args_schema=DeleteRelationshipInput,
    )


def update_relationship_tool(store: GraphStore) -> StructuredTool:
    def update_relationship(
        source: str,
        predicate: str,
        target: str,
        new_predicate: str | None = None,
        new_source: str | None = None,
        new_target: str | None = None,
    ) -> dict[str, Any]:
        return store.update_relationship(source, predicate, target, new_predicate, new_source, new_target)

    return StructuredTool.from_function(
        update_relationship,
        name="update_relationship",
        description="Update one existing relationship without deleting entities. Use for requests such as 'change contains to owns' or 'make Facility supply Well instead'. Identify the existing relationship by source, predicate, and target.",
        args_schema=UpdateRelationshipInput,
    )


def merge_entities_tool(store: GraphStore) -> StructuredTool:
    def merge_entities(source_entity_id: str, target_entity_id: str, merged_name: str | None = None) -> dict[str, Any]:
        return store.merge_entities(source_entity_id, target_entity_id, merged_name)

    return StructuredTool.from_function(
        merge_entities,
        name="merge_entities",
        description="Merge duplicate entities. The source entity is removed, its relationships are rewired to the target entity, and source properties are copied to the target.",
        args_schema=MergeEntitiesInput,
    )


def clear_graph_tool(store: GraphStore) -> StructuredTool:
    def clear_graph(reason: str) -> dict[str, int] | dict[str, bool | str]:
        approval = interrupt(
            {
                "title": "Clear graph?",
                "message": "This will delete all entities and relationships from the current graph.",
                "reason": "clear_graph_confirmation",
                "request_reason": reason,
                "details": {"entities": len(store.nodes), "relationships": len(store.edges)},
            }
        )
        if not isinstance(approval, dict) or approval.get("approved") is not True:
            return {"cancelled": True, "message": "Clear graph cancelled by user."}
        return store.clear_graph()

    return StructuredTool.from_function(
        clear_graph,
        name="clear_graph",
        description="Request human approval to delete every entity and relationship in the graph. Use when the user asks to delete all entities, clear the graph, reset the model, remove everything, or start over. The model supplies a reason; the human supplies approval.",
        args_schema=ClearGraphInput,
    )


def set_namespace_tool(store: GraphStore) -> StructuredTool:
    def set_namespace(prefix: str, namespace: str) -> dict[str, str]:
        return store.set_namespace(prefix, namespace)

    return StructuredTool.from_function(
        set_namespace,
        name="set_namespace",
        description="Set the Turtle prefix and namespace used for generated OWL classes and properties. Use when the user asks to change the namespace, base IRI, entity IRI namespace, or prefix.",
        args_schema=SetNamespaceInput,
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
            "Include concise descriptions when the source explains what an entity means. Prefer singular entity names such as 'Well' instead of 'Wells'."
        ),
        args_schema=ApplyGraphOperationsInput,
    )


def list_graph_tool(store: GraphStore) -> StructuredTool:
    def list_graph() -> dict[str, list[dict[str, Any]]]:
        return store.list_graph()

    return StructuredTool.from_function(
        list_graph,
        name="list_graph",
        description="Read the current graph state without changing it. Use before edits when the current entities or relationships are unclear.",
    )


def save_model_tool(store: GraphStore) -> StructuredTool:
    def save_model(name: str | None = None) -> dict[str, Any]:
        model_name = name or "semantic_model"
        clean_name = model_name.strip().replace(" ", "_")
        filename = clean_name if clean_name.endswith(".ttl") else f"{clean_name}.ttl"
        entity_count = len(store.nodes)
        relationship_count = len(store.edges)
        return {
            "saved": model_name,
            "filename": filename,
            "entity_count": entity_count,
            "relationship_count": relationship_count,
            "message": f"Model '{model_name}' saved with {entity_count} entities and {relationship_count} relationships. A save/download prompt has been presented.",
        }

    return StructuredTool.from_function(
        save_model,
        name="save_model",
        description="Save the current model with an optional name. The model is persisted and can be exported as OWL/Turtle RDF. Use when the user asks to save the model, save as RDF, export RDF, or download the Turtle file.",
        args_schema=SaveModelInput,
    )


def save_speckit_tool(store: GraphStore) -> StructuredTool:
    def save_speckit(name: str | None = None) -> dict[str, Any]:
        spec_name = name or "spec"
        clean_name = spec_name.strip().replace(" ", "_")
        filename = clean_name if clean_name.endswith(".md") else f"{clean_name}.md"
        entity_count = len(store.nodes)
        relationship_count = len(store.edges)
        return {
            "saved": spec_name,
            "filename": filename,
            "entity_count": entity_count,
            "relationship_count": relationship_count,
            "message": f"Spec-kit specification '{spec_name}' generated from {entity_count} entities and {relationship_count} relationships. A save/download prompt has been presented.",
        }

    return StructuredTool.from_function(
        save_speckit,
        name="save_speckit",
        description=(
            "Generate a spec-kit-compatible feature specification (spec.md) from the current ontology so it can seed "
            "a spec-kit /plan and /tasks workflow to build the data product. Use when the user asks to save as speckit, "
            "export a spec-kit spec, or generate a data product specification."
        ),
        args_schema=SaveSpeckitInput,
    )


def modelling_tools(store: GraphStore) -> list[StructuredTool]:
    return [
        create_entity_tool(store),
        create_relationship_tool(store),
        add_property_tool(store),
        update_entity_tool(store),
        delete_entity_tool(store),
        delete_relationship_tool(store),
        update_relationship_tool(store),
        merge_entities_tool(store),
        clear_graph_tool(store),
        set_namespace_tool(store),
        apply_graph_operations_tool(store),
        save_model_tool(store),
        save_speckit_tool(store),
        list_graph_tool(store),
    ]
