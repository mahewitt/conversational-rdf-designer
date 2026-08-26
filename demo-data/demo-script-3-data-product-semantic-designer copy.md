# Demo Script 3: Data Product Semantic Designer

## Goal

Show VibeGraph as a semantic design assistant for a data architecture audience.

## Script

User:

```text
Create a semantic model for a drilling analytics data product.
```

Expected result:

- Data Product appears on the graph.
- Supporting concepts such as Source System, Consumer, and Quality Rule can be added by the agent.

User:

```text
Add lineage relationships.
```

Expected result:

- The graph gains lineage-oriented relationships between source, data product, and consumer concepts.

User:

```text
Show dependencies.
```

Expected result:

- The assistant explains the graph dependencies in plain language.

User:

```text
Export RDF.
```

Expected result:

- Turtle RDF is available from the RDF preview/export flow.
