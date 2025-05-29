from datetime import datetime
from uuid import uuid4

from app.configs.constants import PROVIDERS, WS_MESSAGES
from app.configs.database import async_session
from app.dtos import WsMessageDto
from app.models import Guest, GuestInfo
from app.pydantic_agents import invoke_agent
from app.repositories import guest_info_repository, guest_repository
from app.services.connection_manager import manager
from app.utils.agent_utils import MessagePart
from fastapi import WebSocket
from pydantic import BaseModel


class ChatResponse(BaseModel):
    guest_id: str
    content: dict
    created_at: str = datetime.now().isoformat()
    id: str = str(uuid4())


async def check_insert_guest(guest_id: str):
    async with async_session() as session:
        try:
            guest = await guest_repository.get_guest_by_id(session, guest_id)
            if not guest:
                guest = Guest(id=guest_id, provider=PROVIDERS.WEB)
                guest_info = GuestInfo(guest_id=guest_id)
                await guest_repository.insert_guest(session, guest)
                await guest_info_repository.insert_guest_info(session, guest_info)
                await session.commit()
            return guest
        except Exception as e:
            await session.rollback()
            raise e


async def handle_test_chat(websocket: WebSocket, data: dict):
    try:
        guest_id = data.get("id")
        await check_insert_guest(guest_id)
        message_parts: list[MessagePart] = await invoke_agent(guest_id, data["message"])
    except Exception as e:
        pass
    for part in message_parts:
        content = {
            "side": "staff",
        }
        if part.type == "text" or part.type == "link":
            response = {"text": part.payload}
        else:
            response = {
                "attachments": [
                    {
                        "type": part.type,
                        "payload": {
                            "url": part.payload,
                        },
                    }
                ]
            }
        content["message"] = response
        chat_response = ChatResponse(
            guest_id=data["id"],
            content=content,
        )
        await manager.send_message(
            websocket,
            WsMessageDto(
                message=WS_MESSAGES.TEST_CHAT, data=chat_response.model_dump()
            ),
        )
