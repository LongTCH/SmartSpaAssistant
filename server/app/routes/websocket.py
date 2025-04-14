from fastapi import APIRouter
from app.services.connection_manager import manager
from fastapi import WebSocket, WebSocketDisconnect
from app.configs import constants

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            # Handle incoming message
            print("Received message:", message)
            response = {
                "message": constants.CONNECTED,
                "data": {"status": 200, "message": "Connected to WebSocket"}
            }
            await manager.broadcast(response)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
