import pytest

from app.graph_store import GraphStore


def test_graph_store_supports_entities_relationships_and_properties() -> None:
    store = GraphStore()

    facility = store.create_entity("Facility")
    well = store.create_entity("Well")
    relationship = store.create_relationship(facility["id"], "contains", well["id"])
    store.add_property(facility["id"], "name", "North")

    assert relationship["label"] == "contains"
    assert store.nodes[0]["data"]["properties"] == {"name": "North"}
    assert len(store.edges) == 1


def test_delete_entity_removes_connected_relationships() -> None:
    store = GraphStore()
    facility = store.create_entity("Facility")
    well = store.create_entity("Well")
    store.create_relationship(facility["id"], "contains", well["id"])

    store.delete_entity(well["id"])

    assert [node["id"] for node in store.nodes] == ["facility"]
    assert store.edges == []


def test_delete_relationship_removes_edge_without_deleting_entities() -> None:
    store = GraphStore()
    facility = store.create_entity("Facility")
    well = store.create_entity("Well")
    store.create_relationship(facility["id"], "contains", well["id"])

    result = store.delete_relationship(facility["id"], "contains", well["id"])

    assert result == {"deleted_relationships": 1}
    assert {node["id"] for node in store.nodes} == {"facility", "well"}
    assert store.edges == []


def test_delete_relationship_returns_zero_when_edge_does_not_exist() -> None:
    store = GraphStore()
    store.create_entity("Facility")
    store.create_entity("Well")

    result = store.delete_relationship("facility", "contains", "well")

    assert result == {"deleted_relationships": 0}


def test_clear_graph_removes_all_entities_and_relationships() -> None:
    store = GraphStore()
    facility = store.create_entity("Facility")
    well = store.create_entity("Well")
    store.create_relationship(facility["id"], "contains", well["id"])

    result = store.clear_graph()

    assert result == {"deleted_entities": 2, "deleted_relationships": 1}
    assert store.nodes == []
    assert store.edges == []


def test_update_entity_requires_an_existing_entity() -> None:
    store = GraphStore()

    with pytest.raises(ValueError, match="does not exist"):
        store.update_entity("missing", "Renamed")


def test_update_relationship_changes_predicate() -> None:
    store = GraphStore()
    facility = store.create_entity("Facility")
    well = store.create_entity("Well")
    store.create_relationship(facility["id"], "contains", well["id"])

    edge = store.update_relationship("facility", "contains", "well", new_predicate="owns")

    assert edge["label"] == "owns"
    assert store.edges == [edge]


def test_merge_entities_rewires_relationships_and_removes_duplicate() -> None:
    store = GraphStore()
    production = store.create_entity("Production")
    production_data = store.create_entity("Production Data")
    data_product = store.create_entity("Data Product")
    store.add_property(production["id"], "unit", "daily")
    store.create_relationship(production["id"], "is stored in", data_product["id"])
    store.create_relationship(production_data["id"], "is stored in", data_product["id"])

    merged = store.merge_entities("production", "production-data", "Production Data")

    assert merged["id"] == "production-data"
    assert merged["data"]["properties"] == {"unit": "daily"}
    assert {node["id"] for node in store.nodes} == {"production-data", "data-product"}
    assert [{"source": edge["source"], "label": edge["label"], "target": edge["target"]} for edge in store.edges] == [
        {"source": "production-data", "label": "is stored in", "target": "data-product"}
    ]


def test_list_graph_returns_current_state() -> None:
    store = GraphStore()
    store.create_entity("Facility")

    assert store.list_graph() == store.to_state()


def test_set_namespace_updates_prefix_and_namespace() -> None:
    store = GraphStore()

    namespace = store.set_namespace("prod:", "https://example.com/production")

    assert namespace == {"prefix": "prod", "namespace": "https://example.com/production#"}
    assert store.to_state()["namespace"] == namespace


def test_apply_graph_operations_creates_entities_before_relationships() -> None:
    store = GraphStore()

    result = store.apply_graph_operations(
        entities=[
            {"name": "Facility"},
            {"name": "Well"},
            {"name": "Hydrocarbon"},
            {"name": "Sensor"},
            {"name": "Production"},
            {"name": "Data Product"},
        ],
        relationships=[
            {"source": "Facility", "predicate": "contains", "target": "Well"},
            {"source": "Well", "predicate": "produces", "target": "Hydrocarbon"},
            {"source": "Sensor", "predicate": "measures", "target": "Production"},
            {"source": "Production", "predicate": "is stored in", "target": "Data Product"},
        ],
    )

    assert {node["id"] for node in store.nodes} == {"facility", "well", "hydrocarbon", "sensor", "production", "data-product"}
    assert len(result["relationships"]) == 4
    assert {edge["source"] for edge in store.edges} >= {"facility", "well", "sensor", "production"}
