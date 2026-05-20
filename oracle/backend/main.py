"""O.R.A.C.L.E — FastAPI Server"""
from __future__ import annotations

import asyncio
import json
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger

from .orchestrator import OracleOrchestrator
from .jarvis.core import JarvisCore
from .jarvis.design_session import run_design_session


# ------------------------------------------------------------------
# WebSocket connection manager
# ------------------------------------------------------------------

class WebSocketManager:
    def __init__(self):
        self.connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.add(ws)
        logger.info(f"WebSocket connected ({len(self.connections)} total)")

    def disconnect(self, ws: WebSocket):
        self.connections.discard(ws)
        logger.info(f"WebSocket disconnected ({len(self.connections)} remaining)")

    async def broadcast(self, message: dict):
        dead: set[WebSocket] = set()
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.connections -= dead

    @property
    def count(self) -> int:
        return len(self.connections)


# ------------------------------------------------------------------
# Global instances
# ------------------------------------------------------------------

ws_manager = WebSocketManager()
orchestrator: OracleOrchestrator | None = None
jarvis: JarvisCore | None = None
_jarvis_phase: str = "idle"  # idle | building | ready


# ------------------------------------------------------------------
# Lifespan
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    logger.info("O.R.A.C.L.E booting up...")
    orchestrator = OracleOrchestrator(ws_manager)
    await orchestrator.initialize()
    await orchestrator.start()
    yield
    logger.info("O.R.A.C.L.E shutting down...")
    if orchestrator:
        await orchestrator.stop()


# ------------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------------

app = FastAPI(
    title="O.R.A.C.L.E",
    description="Orchestrated Research Agents for Collective Learning and Exploration",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# WebSocket endpoint
# ------------------------------------------------------------------

@app.websocket("/ws/dashboard")
async def websocket_dashboard(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        # Send full system state on connect
        state = await orchestrator.get_system_state()
        await ws.send_json({
            "type": "system_state",
            "data": state,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep alive — echo any incoming messages and send pings on timeout
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await ws.send_json({
                    "type": "ping",
                    "data": {},
                    "timestamp": datetime.utcnow().isoformat(),
                })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(ws)


# ------------------------------------------------------------------
# REST API endpoints
# ------------------------------------------------------------------

@app.get("/api/status")
async def get_status():
    """Return high-level system status."""
    uptime = 0.0
    if orchestrator and orchestrator.start_time:
        import time
        uptime = time.time() - orchestrator.start_time
    return JSONResponse({
        "status": "running" if (orchestrator and orchestrator.running) else "stopped",
        "uptime_seconds": uptime,
        "agent_count": len(orchestrator.agents) if orchestrator else 0,
        "ws_connections": ws_manager.count,
    })


@app.get("/api/agents")
async def get_agents():
    """Return the current state of all agents."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return JSONResponse(orchestrator.get_agents_list())


@app.get("/api/knowledge")
async def get_knowledge(limit: int = 20, min_importance: int = 0):
    """Return knowledge entries filtered by importance."""
    if not orchestrator or not orchestrator.knowledge_base:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    entries = await orchestrator.knowledge_base.get_entries(
        limit=limit, min_importance=min_importance
    )
    return JSONResponse([e.model_dump() for e in entries])


@app.get("/api/discoveries")
async def get_discoveries(limit: int = 20):
    """Return discoveries ordered by breakthrough level."""
    if not orchestrator or not orchestrator.knowledge_base:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    discoveries = await orchestrator.knowledge_base.get_discoveries(limit=limit)
    return JSONResponse([d.model_dump() for d in discoveries])


@app.get("/api/metrics")
async def get_metrics():
    """Return current system metrics."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return JSONResponse(await orchestrator.get_metrics())


@app.post("/api/oracle/start")
async def oracle_start():
    """Start the orchestrator if it is currently stopped."""
    global orchestrator
    if orchestrator and orchestrator.running:
        return JSONResponse({"status": "already_running"})
    if not orchestrator:
        orchestrator = OracleOrchestrator(ws_manager)
        await orchestrator.initialize()
    await orchestrator.start()
    return JSONResponse({"status": "started"})


@app.post("/api/oracle/stop")
async def oracle_stop():
    """Stop the orchestrator."""
    if not orchestrator:
        return JSONResponse({"status": "not_running"})
    await orchestrator.stop()
    return JSONResponse({"status": "stopped"})


@app.post("/api/oracle/challenge")
async def oracle_challenge(body: dict):
    """Assign a custom research challenge to 3 random agents."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    challenge = body.get("challenge", "").strip()
    if not challenge:
        raise HTTPException(status_code=400, detail="'challenge' field is required")

    all_ids = list(orchestrator.agents.keys())
    chosen = random.sample(all_ids, min(3, len(all_ids)))
    for agent_id in chosen:
        agent = orchestrator.agents.get(agent_id)
        if agent:
            await agent.assign_task(challenge)

    return JSONResponse({"status": "assigned", "agents": chosen})


# ------------------------------------------------------------------
# JARVIS endpoints
# ------------------------------------------------------------------

@app.get("/api/jarvis/status")
async def jarvis_status():
    return JSONResponse({
        "phase": _jarvis_phase,
        "online": _jarvis_phase == "ready",
    })


@app.post("/api/jarvis/build")
async def jarvis_build():
    global jarvis, _jarvis_phase
    if _jarvis_phase != "idle":
        return JSONResponse({"status": _jarvis_phase})

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    _jarvis_phase = "building"

    async def _run():
        global jarvis, _jarvis_phase
        try:
            await run_design_session(orchestrator._broadcast_ws)
            jarvis = JarvisCore(orchestrator.knowledge_base)
            jarvis.set_orchestrator(orchestrator)
            orchestrator.set_jarvis(jarvis)
            _jarvis_phase = "ready"
        except Exception as exc:
            logger.error(f"JARVIS build failed: {exc}")
            _jarvis_phase = "idle"

    asyncio.create_task(_run())
    return JSONResponse({"status": "building"})


@app.post("/api/jarvis/chat")
async def jarvis_chat(body: dict):
    global jarvis
    if not jarvis:
        raise HTTPException(status_code=503, detail="J.A.R.V.I.S n'est pas encore en ligne")

    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="'message' requis")

    result = await jarvis.chat(message)

    # Broadcast JARVIS message so activity feed shows it
    await orchestrator._broadcast_ws("jarvis_message", {
        "content": result["content"],
        "dispatches": result["dispatches"],
        "timestamp": result["timestamp"],
    })

    return JSONResponse(result)


@app.get("/api/jarvis/conversation")
async def jarvis_conversation():
    if not jarvis:
        return JSONResponse([])
    return JSONResponse(jarvis.get_conversation())


# ------------------------------------------------------------------
# Static files — serve frontend build if it exists
# ------------------------------------------------------------------

FRONTEND_BUILD = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_BUILD.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_BUILD / "assets"),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(FRONTEND_BUILD / "index.html")


# ------------------------------------------------------------------
# Direct execution
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("oracle.backend.main:app", host="0.0.0.0", port=8000, reload=False)
