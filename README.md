# VibeGraph

VibeGraph is a conversational semantic modelling prototype. This repository contains the **hour-1 solution** from the hackathon proposal: a CopilotKit chat connected to a deterministic LangGraph agent through the AG-UI protocol, a React Flow shared graph canvas, and a live RDF state preview.

## Prerequisites

- Python 3.11+
- `uv` ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- Node.js 18.18+

## Run the backend

```powershell
cd backend
uv sync --dev
uv run uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Check it with `http://localhost:8000/health`.

### Enable the LLM

The backend uses the configured OpenAI-compatible deployment when these values are present in `backend/.env`:

```dotenv
OPENAI_ENDPOINT=https://your-openai-compatible-endpoint/
OPENAI_API_KEY=your-key
OPENAI_DEPLOYMENT=your-deployment
```

Then start the backend as usual:

```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

The LangGraph agent binds the graph tools to this model, loops through model and tool nodes until the model stops requesting tools, and streams the updated graph and RDF state through AG-UI. The backend raises a clear configuration error if these values are missing, so it does not silently run a local deterministic substitute. Tests mock the model instead of calling a live deployment. Do not commit `backend/.env` or put keys in `NEXT_PUBLIC_*` variables.

## Run the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`, type a modelling instruction, and send it. CopilotKit talks to the local Next.js runtime route, which forwards the AG-UI request to the Python LangGraph agent. Assistant messages and shared graph state stream back through the runtime; the canvas and RDF preview update from that state.

## Development versus deployment

Use the Next.js development server while building the frontend:

```powershell
cd frontend
npm run dev
```

This provides fast refresh and useful development errors. You do not need to generate a static build after every code change.

When you are ready to test or deploy the frontend, create a production build:

```powershell
cd frontend
npm run build
```

The current frontend build is served through Next.js because the CopilotKit Runtime route is a server-side route. A future static-export configuration could host only the visual frontend, but it would need a separately deployed CopilotKit Runtime or another compatible runtime endpoint. The Python backend is still required for agent responses and streaming graph updates.

The deployed arrangement would be:

```text
Browser
	|
	v
CopilotKit Runtime (Next.js `/api/copilotkit`)
	|
	| AG-UI / SSE
	v
FastAPI + LangGraph agent
```

For local development, run both servers: Next.js on `http://localhost:3000` and FastAPI on `http://localhost:8000`.

## Verify the hour-1 smoke test

```powershell
cd backend
uv run pytest
```

Full document extraction remains planned for hours 4-5.

## Hour-1 architecture

The frontend uses `CopilotKit` and `CopilotChat` for the conversation runtime. `useCoAgent` projects the backend's shared state into the page; React Flow renders its `nodes` and `edges`, while the RDF panel renders its `rdf` field.

The backend compiles a `LangGraph` state graph and exposes it through `ag-ui-langgraph` at `POST http://localhost:8000/api/agent`. The graph uses a standard model/tool loop: call the model, run requested semantic tools, return to the model, and finish when there are no more tool calls. The Next.js CopilotKit Runtime registers that endpoint as a server-side `HttpAgent` and exposes `/api/copilotkit` to the browser. The runtime handles agent discovery, routing, and the CopilotKit-to-AG-UI boundary. An in-memory LangGraph checkpointer provides thread state during the process lifetime; persistent storage remains out of scope for the hackathon.

## Hour 2: graph store and tools

The hour-2 layer is implemented in `backend/app/graph_store.py` and `backend/app/semantic_tools.py`. `GraphStore` is the authoritative in-memory model for nodes and relationships. The semantic tools expose create entity, create relationship, add property, update entity, and delete entity operations as LangChain `StructuredTool` instances. The LangGraph modelling node invokes these tools, then derives RDF from the resulting graph state. Deleting an entity also removes its connected relationships.

Run the focused hour-2 tests with:

```powershell
cd backend
uv run pytest tests/test_graph_store.py tests/test_stream.py
```

## Hour 3: LangGraph agent

The hour-3 agent is implemented as a LangGraph model/tool loop in `backend/app/graph.py`:

```text
call_model -> run_tools -> call_model -> emit_state
```

The model receives the conversation messages and the system prompt, can call semantic tools, and loops until it returns a final assistant message with no further tool calls. The final `emit_state` node publishes the updated graph and RDF state through AG-UI. The backend tests mock the model to verify the required conversation flow:

```text
Create Facility
Create Well
Facility contains Well
```

That test confirms conversation turns create graph state through the same tool path used by the real LLM.

## Hour 4: document extraction

Document-style prompts are handled through the `apply_graph_operations` semantic tool. The model extracts a batch of entities, relationships, and attributes, then the backend applies them in dependency-safe order:

```text
1. Create all entities
2. Create all relationships
3. Add attributes
```

This avoids relationship failures when a model identifies a relationship before emitting the corresponding entity creation. For example, `Production is stored in Data Product` succeeds when the extracted entity batch also contains `Production` and `Data Product`.
