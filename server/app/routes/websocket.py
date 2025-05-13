from app.baml_agents import invoke_agent
from app.configs.constants import WS_MESSAGES
from app.dtos import WsMessageDto
from app.services.connection_manager import manager
from app.utils.asyncio_utils import run_background
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

ws_router = APIRouter()


class ChatResponse(BaseModel):
    id: str
    message: str


async def handle_test_chat(websocket: WebSocket, data: dict):
    try:
        response = await invoke_agent(data["id"], data["message"])
    except Exception as e:
        response = f"**Error:** {str(e)}"
    chat_response = ChatResponse(
        id=data["id"],
        message=response,
    )
    await manager.send_message(
        websocket,
        WsMessageDto(message=WS_MESSAGES.TEST_CHAT, data=chat_response.model_dump()),
    )


@ws_router.websocket("/ws")
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
