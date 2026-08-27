# Demo Script 3: Data Product Semantic Designer

## Goal

Show VibeGraph as a semantic design assistant for a data architecture audience.

## Script

- create a sample retail ontology

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


- describe the ontology so far
- save as RDF
