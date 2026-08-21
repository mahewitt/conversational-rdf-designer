"""VibeGraph's FastAPI host for the LangGraph AG-UI agent."""

from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .graph import model_graph

app = FastAPI(title="VibeGraph Agent", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent = LangGraphAgent(name="vibegraph", graph=model_graph, emit_raw_events=False)
add_langgraph_fastapi_endpoint(app, agent, path="/api/agent")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}



