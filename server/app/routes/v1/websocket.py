from app.configs.constants import WS_MESSAGES
from app.dtos import WsMessageDto
from app.services.connection_manager import manager
from app.services.integrations.test_chat_service import handle_test_chat
from app.utils.asyncio_utils import run_background
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()


@ws_router.websocket("/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = WsMessageDto(**data)

            if message.message == WS_MESSAGES.CONNECTED:
                await websocket.send_json(
                    {
                        "type": WS_MESSAGES.CONNECTED,
                        "message": "Connected to WebSocket",
                    }
                )
            elif message.message == WS_MESSAGES.TEST_CHAT:
                run_background(handle_test_chat, websocket, message.data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
