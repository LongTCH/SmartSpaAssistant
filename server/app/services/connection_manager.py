from app.dtos import WsMessageDto
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass  # Connection already removed

    async def broadcast(self, message: WsMessageDto):
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message.__dict__)
            except Exception:
                # Connection is broken, mark for removal
                disconnected_connections.append(connection)

        # Remove broken connections
        for connection in disconnected_connections:
            try:
                self.active_connections.remove(connection)
            except ValueError:
                pass  # Connection already removed

    async def send_message(self, websocket: WebSocket, message: WsMessageDto):
        try:
            await websocket.send_json(message.__dict__)
        except Exception:
            # Connection is broken, remove it
            self.disconnect(websocket)


manager = ConnectionManager()
