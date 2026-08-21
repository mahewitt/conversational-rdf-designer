# Demo Script 1: Simple Conversational Modelling

## Goal

Show that plain language can create and refine a semantic graph.

## Script

User:

```text
Create Facility.
```

Expected result:

- Facility entity appears on the graph.

User:

```text
Create Well.
```

Expected result:

- Well entity appears on the graph.

User:

```text
Facility contains Well.
```

Expected result:

- A `contains` relationship appears from Facility to Well.

User:

```text
Add Production Measurement.
```

Expected result:

- Production Measurement appears on the graph.
- The graph state and RDF preview update.

User:

```text
Export RDF.
```

Expected result:

- Turtle RDF is available from the RDF preview/export flow.
