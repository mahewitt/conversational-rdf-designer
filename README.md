# VibeGraph

VibeGraph is a conversational semantic modelling prototype. This repository contains the **hour-1 skeleton** from the hackathon proposal: a streaming Python agent endpoint, a chat surface, a React Flow shared graph canvas, and an RDF preview placeholder.

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

Open `http://localhost:3000`, type a modelling instruction, and send it. The backend streams assistant messages, a tool event, and a shared graph state; the canvas updates when the state event arrives.

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

The current frontend build is still served through Next.js. A future static-export configuration can generate an `out/` directory that can be hosted by a static hosting service without running a Node.js server. Static hosting only removes the Node.js server requirement for the frontend; the Python backend is still required for agent responses and streaming graph updates.

The deployed arrangement would be:

```text
Static frontend hosting
	|
	| HTTP and SSE requests
	v
Deployed FastAPI backend
```

For local development, run both servers: Next.js on `http://localhost:3000` and FastAPI on `http://localhost:8000`.

## Verify the hour-1 smoke test

```powershell
cd backend
uv run pytest
```

The current agent response is deterministic so the skeleton can be demonstrated without Azure OpenAI credentials. The `agent_events` boundary in `backend/app/main.py` is the intended insertion point for the LangGraph and CopilotKit/AG-UI adapter in the next hour. RDF generation and semantic tools are intentionally placeholders for hours 2-5.
