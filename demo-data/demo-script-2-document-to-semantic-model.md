# Demo Script 2: Document to Semantic Model

## Goal

Show that a short business description can be converted into graph structure.

## Script

User:

```text
Extract entities and relationships:

A facility contains multiple wells.
Wells produce hydrocarbons.
Sensors measure production.
Production data is stored in a data product.
```

Expected result:

- Facility, Well, Hydrocarbon, Sensor, Production, Production Data, and Data Product concepts are identified.
- Relationships such as `contains`, `produce`, `measure`, and `stored in` are added where supported by the current tools.
- React Flow renders the graph state.
- The RDF preview updates from the current graph.

User:

```text
Rename Production Data to Production Measurement.
```

Expected result:

- The graph updates the relevant entity label.
- The RDF preview reflects the renamed concept.

User:

```text
Export RDF.
```

Expected result:

- Turtle RDF is available from the RDF preview/export flow.
