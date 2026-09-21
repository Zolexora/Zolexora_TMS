import json
import logging
import uuid
from typing import Any, Dict, List
from fastapi import WebSocket

logger = logging.getLogger("zolexora.websocket")


class ConnectionManager:
    def __init__(self):
        # Maps organisation_id -> List of active WebSockets
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: uuid.UUID):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = []
        self.active_connections[org_id].append(websocket)
        logger.info(f"WebSocket connected for org {org_id} (total: {len(self.active_connections[org_id])})")

    def disconnect(self, websocket: WebSocket, org_id: uuid.UUID):
        if org_id in self.active_connections:
            if websocket in self.active_connections[org_id]:
                self.active_connections[org_id].remove(websocket)
            if not self.active_connections[org_id]:
                del self.active_connections[org_id]
        logger.info(f"WebSocket disconnected for org {org_id}")

    async def broadcast_to_org(self, org_id: uuid.UUID, event_type: str, data: Dict[str, Any]):
        """Broadcasts an operational event strictly to connected clients belonging to the target organisation."""
        if org_id not in self.active_connections:
            return

        payload = json.dumps({
            "event": event_type,
            "organisation_id": str(org_id),
            "data": data,
        })

        dead_sockets = []
        for socket in self.active_connections[org_id]:
            try:
                await socket.send_text(payload)
            except Exception as e:
                logger.warning(f"Error sending WebSocket event {event_type}: {e}")
                dead_sockets.append(socket)

        for ds in dead_sockets:
            self.disconnect(ds, org_id)


ws_manager = ConnectionManager()
