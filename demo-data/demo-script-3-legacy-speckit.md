# Demo Script 3: Data Product Semantic Designer

## Goal

Supports converting legacy ER diagrams, UML class diagrams, database schemas, or conceptual model images. So if have diagram in ppt can convert easily

## Script

- Clear any old designs

User:

```text
clear all
```

Expected result:

- HITL confirmation then clear.

### create an ontology. 

User:

- drag er-example.png
```text
create an ontology from this
```

Expected result:

- ontology

### Cleanup 

User (if needed):

```text
cyber cash can also have a registered credit card
```

```text
xxx should be conected to xxx not xxx
```

Expected result:

- Fixes implemented


### SpecKit

User:
One of the powers of such an ontology is it can be used for many purposes - from describing the business to a real artifact that drives and guides AI. Now we have an ontology, I can export it as a spec-kit specification. That means an engineering team can hand this file straight to their AI coding agent, run /plan and /tasks, and go from semantic model to a working data product — schema, API, pipeline or agent — without re-typing a single requirement. The ontology is the spec."

```text
Save as speckit
```

Expected result:

- File saved as speckit markdown for use in a speckit project
