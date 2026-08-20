"""VibeGraph's hour-one streaming agent host."""

import asyncio
import json
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


DEMO_GRAPH = {
    "nodes": [
        {"id": "facility", "label": "Facility", "kind": "entity", "position": {"x": 120, "y": 150}},
        {"id": "well", "label": "Well", "kind": "entity", "position": {"x": 430, "y": 280}},
        {"id": "measurement", "label": "Production Measurement", "kind": "measurement", "position": {"x": 720, "y": 150}},
    ],
    "edges": [
        {"id": "facility-contains-well", "source": "facility", "target": "well", "label": "contains"},
        {"id": "well-produces-measurement", "source": "well", "target": "measurement", "label": "produces"},
    ],
}


app = FastAPI(title="VibeGraph Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def event(event_type: str, payload: object) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"


async def agent_events(message: str) -> AsyncIterator[str]:
    """Temporary deterministic stream; replace its decision layer with LangGraph in hour 3."""
    yield event("run_started", {"message": message})
    await asyncio.sleep(0.15)
    yield event("assistant_message", {"content": "I'm shaping that into a semantic model."})
    await asyncio.sleep(0.15)
    yield event("tool_event", {"tool": "update_shared_graph", "status": "completed"})
    await asyncio.sleep(0.15)
    yield event("state_update", {"graph": DEMO_GRAPH})
    yield event("assistant_message", {"content": "The shared graph is ready for your next instruction."})
    yield event("run_finished", {"ok": True})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/agent/stream")
async def stream_agent(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        agent_events(request.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
