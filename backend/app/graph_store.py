"""Authoritative in-memory graph store for semantic modelling operations."""

from typing import Any
from uuid import uuid4


class GraphStore:
    def __init__(self, nodes: list[dict[str, Any]] | None = None, edges: list[dict[str, Any]] | None = None):
        self.nodes = [dict(node) for node in (nodes or [])]
        self.edges = [dict(edge) for edge in (edges or [])]

    def create_entity(self, name: str, kind: str = "entity", position: dict[str, int] | None = None) -> dict[str, Any]:
        node_id = self._identifier(name)
        existing = self._node(node_id)
        if existing:
            return existing
        node = {
            "id": node_id,
            "type": "default",
            "position": position or {"x": 160 + len(self.nodes) * 280, "y": 170},
            "data": {"label": name, "kind": kind},
        }
        self.nodes.append(node)
        return node

    def update_entity(self, entity_id: str, name: str | None = None, properties: dict[str, Any] | None = None) -> dict[str, Any]:
        node = self._node(entity_id)
        if not node:
            raise ValueError(f"Entity '{entity_id}' does not exist")
        if name:
            node.setdefault("data", {})["label"] = name
        if properties:
            node.setdefault("data", {}).setdefault("properties", {}).update(properties)
        return node

    def delete_entity(self, entity_id: str) -> None:
        if not self._node(entity_id):
            raise ValueError(f"Entity '{entity_id}' does not exist")
        self.nodes = [node for node in self.nodes if node["id"] != entity_id]
        self.edges = [edge for edge in self.edges if edge["source"] != entity_id and edge["target"] != entity_id]

    def create_relationship(self, source: str, predicate: str, target: str) -> dict[str, Any]:
        if not self._node(source) or not self._node(target):
            raise ValueError("Both relationship endpoints must exist")
        existing = next((edge for edge in self.edges if edge["source"] == source and edge["target"] == target and edge["label"] == predicate), None)
        if existing:
            return existing
        edge = {"id": f"{source}-{predicate}-{target}-{uuid4().hex[:6]}", "source": source, "target": target, "label": predicate}
        self.edges.append(edge)
        return edge

    def add_property(self, entity_id: str, property_name: str, value: Any = None) -> dict[str, Any]:
        node = self._node(entity_id)
        if not node:
            raise ValueError(f"Entity '{entity_id}' does not exist")
        node.setdefault("data", {}).setdefault("properties", {})[property_name] = value
        return node

    def apply_graph_operations(
        self,
        entities: list[dict[str, Any]] | None = None,
        relationships: list[dict[str, str]] | None = None,
        attributes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        created_entities = []
        created_relationships = []
        updated_entities = []

        for entity in entities or []:
            created_entities.append(self.create_entity(entity["name"], entity.get("kind", "entity")))

        for relationship in relationships or []:
            source = self.create_entity(relationship["source"])
            target = self.create_entity(relationship["target"])
            created_relationships.append(self.create_relationship(source["id"], relationship["predicate"], target["id"]))

        for attribute in attributes or []:
            entity = self.create_entity(attribute["entity"])
            updated_entities.append(self.add_property(entity["id"], attribute["property"], attribute.get("value")))

        return {
            "entities": created_entities,
            "relationships": created_relationships,
            "attributes": updated_entities,
        }

    def to_state(self) -> dict[str, list[dict[str, Any]]]:
        return {"nodes": self.nodes, "edges": self.edges}

    def _node(self, entity_id: str) -> dict[str, Any] | None:
        return next((node for node in self.nodes if node["id"] == entity_id), None)

    @staticmethod
    def _identifier(name: str) -> str:
        return "-".join(name.lower().strip().split())
