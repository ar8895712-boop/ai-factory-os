# ==============================================================
# backend/routers/websocket.py — Live Telemetry WebSocket Endpoint
# ==============================================================
from __future__ import annotations

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.simulation.websocket_manager import ws_hub

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time factory floor telemetry streaming.
    Pushes cycle updates, machine health scores, sensor channels, and alerts.
    """
    await ws_hub.connect(websocket)
    try:
        # Keep connection open and listen for client commands (e.g. ping/heartbeat)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception:
        ws_hub.disconnect(websocket)

