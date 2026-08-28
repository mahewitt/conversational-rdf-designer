# VibeGraph Architecture Diagrams

Two diagrams for demo presentations: a simple story for non-technical audiences, and a detailed technical component diagram.

## 1. Big-picture story (for everyone)

```mermaid
flowchart LR
    A["👤 You describe a domain,<br/>paste a document, or<br/>drop in an ER diagram image"] --> B["💬 Chat"]
    B --> C["🧠 AI Agent<br/>understands what you meant"]
    C --> D["🕸️ Semantic Model<br/>(entities & relationships)"]
    D --> E["🖼️ Live Canvas<br/>visual graph you can see & edit"]
    D --> F["📄 Ontology Export<br/>(OWL / Turtle file)"]
    D --> G["📋 Spec-Kit Export<br/>(spec.md for building a data product)"]
    E --> A
```

**Narrative for the room:** *"You talk to it like a colleague — type, paste, or drop in a picture of a whiteboard diagram. It builds a shared semantic model live on screen. When you're happy, you export it either as a formal ontology, or as a specification an engineering team's AI coding agent can build a real data product from."*

## 2. Technical component diagram (backup slide)

```mermaid
flowchart TB
    User(("👤 User<br/>Browser"))

    subgraph Frontend["🖥️ FRONTEND — Next.js"]
        direction TB
        UI["💬 Chat • 🖼️ Canvas • 📄 RDF/Spec-Kit Preview"]
        CK["🔌 CopilotKit Runtime<br/><small>/api/copilotkit</small>"]
        UI --- CK
    end

    subgraph Backend["⚙️ BACKEND — FastAPI"]
        direction TB
        EP(["🚪 AG-UI Endpoint<br/><small>/api/agent</small>"])

        subgraph Loop["🔁 LangGraph Agent Loop"]
            direction LR
            CM["🧠 call_model"] --> RT["🛠️ run_tools"]
            RT -.-> CM
            CM --> ES["📡 emit_state"]
        end

        LLM[["✨ LLM<br/><small>OpenAI-compatible</small>"]]
        Tools["🧰 Semantic Tools<br/><small>create • update • merge • delete</small>"]
        Store[("🗄️ GraphStore<br/><small>nodes • edges • namespace</small>")]
        RDF["📜 owl_turtle()<br/><small>→ Turtle / RDF</small>"]
        Spec["📋 generate_speckit_spec()<br/><small>→ spec.md</small>"]

        EP --> CM
        CM <--> LLM
        RT --> Tools
        Tools --> Store
        Store --> RDF
        Store --> Spec
    end

    User <--> UI
    CK <==>|AG-UI / SSE| EP
    ES ==>|state snapshot| UI

    classDef user fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f;
    classDef frontend fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e;
    classDef backend fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#4c1d95;
    classDef loop fill:#fce7f3,stroke:#db2777,stroke-width:1.5px,color:#831843;
    classDef store fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d;
    classDef output fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12;

    class User user;
    class UI,CK frontend;
    class EP,LLM,Tools backend;
    class CM,RT,ES loop;
    class Store store;
    class RDF,Spec output;
```

Key visual choices:
- **Color per layer**: amber = user, blue = frontend, purple = backend/agent, pink = the model/tool loop, green = the single source-of-truth store, orange = the two exportable outputs.
- **Shape per role**: rounded pill for entry points, hexagon for the LLM, cylinder for the store — makes the diagram scannable even without reading labels closely.
- **Line style**: dashed for the internal `run_tools → call_model` loop-back, thick double lines (`==>`) for the two "big" cross-boundary hops (AG-UI transport, state snapshot back to the UI), thin lines for internal wiring.
