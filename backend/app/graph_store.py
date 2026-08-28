"""Authoritative in-memory graph store for semantic modelling operations."""

from typing import Any
from uuid import uuid4


class GraphStore:
    def __init__(
        self,
        nodes: list[dict[str, Any]] | None = None,
        edges: list[dict[str, Any]] | None = None,
        namespace: dict[str, str] | None = None,
    ):
        self.nodes = [dict(node) for node in (nodes or [])]
        self.edges = [dict(edge) for edge in (edges or [])]
        self.namespace = namespace or {"prefix": "vg", "namespace": "http://example.com/vibegraph#"}

    def create_entity(self, name: str, description: str | None = None, position: dict[str, int] | None = None) -> dict[str, Any]:
        node_id = self._identifier(name)
        existing = self._node(node_id)
        if existing:
            if description:
                existing.setdefault("data", {})["description"] = description
            return existing
        node = {
            "id": node_id,
            "type": "default",
            "position": position or {"x": 160 + len(self.nodes) * 280, "y": 170},
            "data": {"label": name, "description": description or self._default_description(name)},
        }
        self.nodes.append(node)
        return node

    def update_entity(
        self,
        entity_id: str,
        name: str | None = None,
        description: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        node = self._node(entity_id)
        if not node:
            raise ValueError(f"Entity '{entity_id}' does not exist")
        if name:
            node.setdefault("data", {})["label"] = name
            if description is None:
                node["data"]["description"] = self._default_description(name)
        if description:
            node.setdefault("data", {})["description"] = description
        if properties:
            node.setdefault("data", {}).setdefault("properties", {}).update(properties)
        return node

    def delete_entity(self, entity_id: str) -> None:
        if not self._node(entity_id):
            raise ValueError(f"Entity '{entity_id}' does not exist")
        self.nodes = [node for node in self.nodes if node["id"] != entity_id]
        self.edges = [edge for edge in self.edges if edge["source"] != entity_id and edge["target"] != entity_id]

    def clear_graph(self) -> dict[str, int]:
        deleted_entities = len(self.nodes)
        deleted_relationships = len(self.edges)
        self.nodes = []
        self.edges = []
        return {"deleted_entities": deleted_entities, "deleted_relationships": deleted_relationships}

    def set_namespace(self, prefix: str, namespace: str) -> dict[str, str]:
        clean_prefix = prefix.strip().rstrip(":")
        clean_namespace = namespace.strip()
        if not clean_prefix:
            raise ValueError("Namespace prefix is required")
        if not clean_namespace:
            raise ValueError("Namespace IRI is required")
        if not clean_namespace.endswith(('/', '#')):
            clean_namespace = f"{clean_namespace}#"
        self.namespace = {"prefix": clean_prefix, "namespace": clean_namespace}
        return self.namespace

    def create_relationship(self, source: str, predicate: str, target: str) -> dict[str, Any]:
        if not self._node(source) or not self._node(target):
            raise ValueError("Both relationship endpoints must exist")
        existing = next((edge for edge in self.edges if edge["source"] == source and edge["target"] == target and edge["label"] == predicate), None)
        if existing:
            return existing
        edge = {"id": f"{source}-{predicate}-{target}-{uuid4().hex[:6]}", "source": source, "target": target, "label": predicate}
        self.edges.append(edge)
        return edge

    def delete_relationship(self, source: str, predicate: str, target: str) -> dict[str, int]:
        before = len(self.edges)
        self.edges = [edge for edge in self.edges if not (edge["source"] == source and edge["target"] == target and edge["label"] == predicate)]
        return {"deleted_relationships": before - len(self.edges)}

    def update_relationship(
        self,
        source: str,
        predicate: str,
        target: str,
        new_predicate: str | None = None,
        new_source: str | None = None,
        new_target: str | None = None,
    ) -> dict[str, Any]:
        edge = next((item for item in self.edges if item["source"] == source and item["target"] == target and item["label"] == predicate), None)
        if not edge:
            raise ValueError(f"Relationship '{source} {predicate} {target}' does not exist")
        if new_source and not self._node(new_source):
            raise ValueError(f"Entity '{new_source}' does not exist")
        if new_target and not self._node(new_target):
            raise ValueError(f"Entity '{new_target}' does not exist")
        edge["source"] = new_source or edge["source"]
        edge["target"] = new_target or edge["target"]
        edge["label"] = new_predicate or edge["label"]
        return edge

    def merge_entities(self, source_entity_id: str, target_entity_id: str, merged_name: str | None = None) -> dict[str, Any]:
        source = self._node(source_entity_id)
        target = self._node(target_entity_id)
        if not source or not target:
            raise ValueError("Both merge entities must exist")
        if source_entity_id == target_entity_id:
            return target
        source_properties = source.get("data", {}).get("properties", {})
        target.setdefault("data", {}).setdefault("properties", {}).update(source_properties)
        if merged_name:
            target["data"]["label"] = merged_name
        for edge in self.edges:
            if edge["source"] == source_entity_id:
                edge["source"] = target_entity_id
            if edge["target"] == source_entity_id:
                edge["target"] = target_entity_id
        self.nodes = [node for node in self.nodes if node["id"] != source_entity_id]
        self.edges = self._deduplicate_edges([edge for edge in self.edges if edge["source"] != edge["target"]])
        return target

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
            created_entities.append(self.create_entity(entity["name"], entity.get("description")))

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

    def to_state(self) -> dict[str, Any]:
        return {"nodes": self.nodes, "edges": self.edges, "namespace": self.namespace}

    def list_graph(self) -> dict[str, list[dict[str, Any]]]:
        return self.to_state()

    def _node(self, entity_id: str) -> dict[str, Any] | None:
        return next((node for node in self.nodes if node["id"] == entity_id), None)

    @staticmethod
    def _deduplicate_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        unique_edges = []
        for edge in edges:
            key = (edge["source"], edge["label"], edge["target"])
            if key in seen:
                continue
            seen.add(key)
            unique_edges.append(edge)
        return unique_edges

    @staticmethod
    def _identifier(name: str) -> str:
        return "-".join(name.lower().strip().split())

    @staticmethod
    def _default_description(name: str) -> str:
        # Last-resort placeholder; callers should normally infer and pass a domain-specific description.
        return f"A {name} in this semantic model."
