# Demo Script 2: Document / Web to Ontology

## Goal

Show VibeGraph as a semantic design assistant for a data architecture audience.

## Script

- Clear any old designs

User:

```text
clear all
```

Expected result:

- HITL confirmation then clear.

User (entity and relationship extraction from documents):

```text
create an ontology from: https://www.statkraft.com/energy-technologies/solar-power/
```

Expected result:

- Ontology created
- Find Statcraft entity and show the it contains and owns link

User:

```text
change the namespace to http://equinor.comn/solar
```

Expected result:

- Namespace updated.

User:

```text
what key entities might be missing
```

Expected result:

- List shown

User:

```text
add 1, 2
```

Expected result:

- Entities and relationships added

User:

```text
describe the ontology so far
```

User:

```text
Export RDF.
```

Expected result:

- Turtle RDF is available from the RDF preview/export flow.