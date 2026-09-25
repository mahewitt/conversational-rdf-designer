# VibeGraph Agent Guidance

## Project purpose

VibeGraph is a conversational semantic modelling prototype. Users describe a domain, provide document text or diagrams, and receive an editable graph plus generated OWL/Turtle RDF and Spec-Kit output.

Keep the project focused on this workflow. Prefer small, testable changes that improve modelling correctness, state synchronization, usability, or export quality.

## Technology choices

Use the existing stack unless the task explicitly requires a change:

- Frontend: Next.js 14, React 18, TypeScript, CopilotKit, AG-UI client, and React Flow (`@xyflow/react`).
- Backend: Python 3.11+, FastAPI, Uvicorn, LangGraph, LangChain structured tools, AG-UI, and an OpenAI-compatible chat model.
- Python tooling: `uv` for environments and commands, `pytest` for tests.
- Frontend tooling: `npm` and the scripts in `frontend/package.json`.
- Formatting: Prettier for TypeScript/TSX and Ruff for Python when configured or available.

Do not replace CopilotKit, LangGraph, AG-UI, React Flow, FastAPI, or `GraphStore` with a different framework for convenience. Do not add a database, authentication system, background worker, or deployment platform unless the request calls for it.

## Architecture and ownership

The request and state flow is:

```text
Browser CopilotChat
  -> Next.js /api/copilotkit runtime
  -> AG-UI HttpAgent
  -> FastAPI /api/agent
  -> LangGraph model/tool loop
  -> GraphStore
  -> shared graph state and generated RDF
  -> AG-UI stream back to the browser
```

### Frontend

- `frontend/app/page.tsx` owns the main workspace UI.
- `useAgent({ agentId: "vibegraph" })` reads shared agent state.
- `state.nodes` and `state.edges` drive React Flow.
- `state.rdf` drives the live RDF preview and RDF download.
- `state.speckit` drives Spec-Kit download.
- `frontend/app/copilotkit-provider.tsx` registers the `vibegraph` agent and runtime URL.
- `frontend/app/api/copilotkit/route.ts` is the server-side CopilotKit runtime boundary.

Keep the frontend a projection of agent state. Do not maintain a second independent semantic graph in React state unless there is a clear synchronization design.

React Flow layout changes, such as moving a node, are UI state changes. Semantic changes must go through backend tools so the graph, RDF, and future agent turns remain consistent. If adding direct canvas editing, update all affected state fields and add a focused test or documented limitation.

### Backend

- `backend/app/graph.py` owns LangGraph state, model/tool routing, state emission, and RDF generation.
- `backend/app/graph_store.py` is the authoritative in-memory semantic graph model.
- `backend/app/semantic_tools.py` exposes validated LangChain tools backed by `GraphStore`.
- `backend/app/main.py` exposes the FastAPI health endpoint and AG-UI agent endpoint.
- `backend/app/spec_export.py` owns Spec-Kit generation.
- `backend/app/web_fetch.py` owns URL validation and page text extraction.

Make graph mutations in `GraphStore`, not in the LangGraph orchestration code or frontend. Keep tools thin: validate inputs through Pydantic schemas, call the store, and return useful structured results.

The normal LangGraph loop is:

```text
call_model -> run_tools -> call_model -> emit_state
```

After tool execution, return the store state and regenerate derived outputs such as RDF and Spec-Kit. Do not hand-edit derived RDF as a separate source of truth.

## Graph model rules

- Nodes represent semantic entities and use lowercase hyphenated IDs derived from their names.
- Node display labels live under `node.data.label`.
- Node descriptions live under `node.data.description` and should be concise, domain-specific, one-sentence definitions.
- Optional entity attributes live under `node.data.properties`.
- Edges represent object properties and use `source`, `target`, and `label`.
- Relationship endpoints must resolve to existing node IDs.
- Deleting an entity must also remove its connected relationships.
- Bulk extraction must create entities before relationships, then attributes; use `apply_graph_operations` for multi-fact or document/diagram extraction.
- Preserve namespace configuration and regenerate RDF whenever semantic graph content changes.
- Keep identifiers stable when changing display labels unless the task explicitly requires identifier migration.

When changing the graph contract, update the TypeScript shared-state type, backend `GraphState`, store behavior, serializers/exporters, and relevant tests together.

## Agent and tool behavior

The model should use the narrowest appropriate tool:

- `create_entity` for one entity.
- `create_relationship` only when both endpoints exist.
- `add_property` for an attribute on an existing entity.
- `update_entity`, `delete_entity`, and relationship tools for explicit edits.
- `apply_graph_operations` for extraction or multiple dependent facts.
- `list_graph` when existing state is unclear.
- `clear_graph` only for explicit reset requests; preserve the human approval interrupt.
- `fetch_url` before modelling from a URL; never fabricate page content.
- `save_model` and `save_speckit` for export requests.

Keep the system prompt aligned with tool contracts. If a tool's input or behavior changes, update its Pydantic schema, description, system prompt guidance, implementation, and tests.

## State and persistence

The current graph is in memory and is carried through LangGraph/checkpointer state for the process lifetime. It is not durable application persistence. Do not describe the current save tools as database persistence; they generate downloadable output and report the current model.

Do not introduce silent fallback models or fake graph results. Missing model configuration should remain explicit. Tests should mock the configured model and must not call a live deployment.

## Development commands

Backend setup and tests:

```powershell
cd backend
uv sync --dev
uv run pytest
uv run pytest tests/test_graph_store.py tests/test_stream.py
uv run uvicorn app.main:app --reload --port 8000
```

Frontend setup and checks:

```powershell
cd frontend
npm install
npm run dev
npm run build
```

Run the backend on port 8000 and the frontend on port 3000 for local end-to-end work. Check `http://localhost:8000/health` before debugging agent requests.

## Testing expectations

- Add or update focused tests for behavior changes.
- For `GraphStore` changes, test both successful mutations and invalid references/error messages.
- For LangGraph changes, mock the model and verify the streamed state snapshot, tool sequence, and conversation-turn behavior.
- For frontend changes, run `npm run build`; manually verify the affected interaction when practical.
- Preserve tests that prove entity creation, relationship creation, deletion cleanup, bulk extraction ordering, URL extraction, state streaming, and export behavior.
- Do not weaken tests to make an implementation pass. Fix the behavior or clearly document an intentional contract change.

## Code style and changes

- Keep changes minimal and local to the owning layer.
- Preserve existing public APIs and state field names unless a migration is required.
- Prefer explicit, readable Python and TypeScript over clever abstractions.
- Use existing helpers and patterns before adding new dependencies.
- Avoid unrelated formatting or refactoring churn.
- Add comments only when the code would otherwise require non-obvious reasoning; do not narrate straightforward assignments.
- Use ASCII by default in source and documentation unless existing content requires other characters.
- Keep UI labels and interaction patterns consistent with the existing VibeGraph visual language.

## Security and data handling

- Never commit `backend/.env`, API keys, tokens, or credentials.
- Never put backend secrets in `NEXT_PUBLIC_*` variables or browser-delivered code.
- Keep URL fetching restricted to supported HTTP(S) behavior and preserve existing validation and content limits.
- Treat uploaded documents, images, and fetched web content as untrusted input. Validate tool arguments and avoid executing extracted content.
- Do not log secrets or full sensitive documents unnecessarily.

## Change checklist

Before finishing a change:

1. Identify the owning layer and preserve the state contract.
2. Update the smallest relevant implementation and tests.
3. Run the narrowest focused test first, then broader checks when practical.
4. Run `npm run build` for frontend changes and `uv run pytest` for backend changes.
5. Report any tests or checks that could not run and why.
