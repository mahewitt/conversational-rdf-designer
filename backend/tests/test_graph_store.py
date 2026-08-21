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


def test_update_entity_requires_an_existing_entity() -> None:
    store = GraphStore()

    with pytest.raises(ValueError, match="does not exist"):
        store.update_entity("missing", "Renamed")


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
