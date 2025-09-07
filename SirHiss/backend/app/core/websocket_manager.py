"""
WebSocket connection manager for real-time updates
"""

from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = []
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast_message(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def broadcast_bot_update(self, bot_id: int, data: dict):
        """Broadcast bot status updates to interested clients"""
        message = {
            "type": "bot_update",
            "bot_id": bot_id,
            "data": data,
            "timestamp": data.get("timestamp")
        }
        await self.broadcast_message(message)

    async def broadcast_portfolio_update(self, portfolio_id: int, data: dict):
        """Broadcast portfolio updates to interested clients"""
        message = {
            "type": "portfolio_update", 
            "portfolio_id": portfolio_id,
            "data": data,
            "timestamp": data.get("timestamp")
        }
        await self.broadcast_message(message)

    def subscribe_client(self, client_id: str, subscription_type: str):
        """Subscribe client to specific update types"""
        if client_id in self.client_subscriptions:
            if subscription_type not in self.client_subscriptions[client_id]:
                self.client_subscriptions[client_id].append(subscription_type)

    def get_connected_clients_count(self) -> int:
        """Get the number of connected clients"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()