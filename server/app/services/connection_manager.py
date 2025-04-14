from fastapi import WebSocket
from app.dtos import WsMessageDto


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: WsMessageDto):
        for connection in self.active_connections:
            await connection.send_json(message.__dict__)


manager = ConnectionManager()
