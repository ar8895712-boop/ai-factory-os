# ==============================================================
# backend/simulation/websocket_manager.py — Live WebSocket Hub
# ==============================================================
from __future__ import annotations

import json
from typing import Any, Dict, List, Set
from fastapi import WebSocket


class WebSocketHub:
    """Manages active WebSocket connections and broadcasts live telemetry."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast_json(self, message: Dict[str, Any]) -> None:
        """Sends JSON message to all active clients; silently removes disconnected ones."""
        to_remove = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                to_remove.add(connection)
        self.active_connections.difference_update(to_remove)

    @property
    def client_count(self) -> int:
        return len(self.active_connections)


# Singleton instance
ws_hub = WebSocketHub()

