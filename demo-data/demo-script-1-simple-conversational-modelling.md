# Demo Script 1: Simple Conversational Modelling

## Goal

Show that plain language can create and refine a semantic graph.

## Script


User:

```text
We are working within the subsurface domain
```

Expected result:

- Info message to give details

User:

```text
Create Well
```

Expected result:

- Well entity appears on the graph.

User:

```text
Create Wellbore
```

Expected result:

- Wellbore entity appears on the graph.

User:

```text
Well contains a Wellbore
```

Expected result:

- A `contains` relationship appears from Well to Wellbore.

User:

```text
Export RDF.
```

Expected result:

- Turtle RDF is available from the RDF preview/export flow.
