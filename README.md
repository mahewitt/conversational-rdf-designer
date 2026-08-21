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

The current agent response is deterministic so the solution can be demonstrated without Azure OpenAI credentials. Full semantic tool abstractions, document extraction, and model-backed reasoning remain planned for hours 2-5.

## Hour-1 architecture

The frontend uses `CopilotKit` and `CopilotChat` for the conversation runtime. `useCoAgent` projects the backend's shared state into the page; React Flow renders its `nodes` and `edges`, while the RDF panel renders its `rdf` field.

The backend compiles a deterministic `LangGraph` state graph and exposes it through `ag-ui-langgraph` at `POST http://localhost:8000/api/agent`. The Next.js CopilotKit Runtime registers that endpoint as a server-side `HttpAgent` and exposes `/api/copilotkit` to the browser. The runtime handles agent discovery, routing, and the CopilotKit-to-AG-UI boundary. An in-memory LangGraph checkpointer provides thread state during the process lifetime; persistent storage remains out of scope for the hackathon.
