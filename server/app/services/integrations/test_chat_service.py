import asyncio
import random
from datetime import datetime
from uuid import uuid4

from app.configs.constants import CHAT_SIDES, PROVIDERS, WS_MESSAGES
from app.configs.database import async_session, with_session
from app.dtos import WsMessageDto
from app.models import Guest, GuestInfo
from app.pydantic_agents import invoke_agent
from app.repositories import guest_info_repository, guest_repository
from app.services import chat_service
from app.services.connection_manager import manager
from app.utils.agent_utils import MessagePart
from fastapi import WebSocket
from pydantic import BaseModel

some_random_account_name = [
    "John Doe",
    "Jane Smith",
    "Alice Johnson",
    "Bob Brown",
    "Charlie Davis",
    "Diana Prince",
    "Ethan Hunt",
    "Fiona Gallagher",
    "George Costanza",
    "Hannah Montana",
    "Ian Malcolm",
    "Jack Sparrow",
    "Katherine Pierce",
    "Liam Neeson",
    "Mia Wallace",
    "Noah Centineo",
    "Olivia Pope",
    "Paul Atreides",
    "Quinn Fabray",
    "Rachel Green",
    "Sam Winchester",
    "Tina Belcher",
    "Ursula K. Le Guin",
    "Victor Frankenstein",
    "Winston Churchill",
    "Xena Warrior Princess",
    "Yara Greyjoy",
    "Zoe Saldana" "Hải Yến",
    "Ngọc Lan",
    "Minh Tú",
    "Thanh Hằng",
    "Bích Ngọc",
    "Hồng Nhung",
    "Quỳnh Anh",
    "Thảo Nhi",
    "Kim Chi",
    "Linh Đan",
    "Ngọc Trâm",
    "Hà My",
    "Phương Thảo",
    "Diễm My",
    "Thúy Hằng",
    "Ngọc Bích",
]

SENDER_ACTION = {
    "mark_seen": "mark_seen",
    "typing_on": "typing_on",
    "typing_off": "typing_off",
}
RESEND_TYPING_AFTER = 8  # seconds


async def send_action(guest_id: str, websocket: WebSocket, action: str):
    """
    Sends an action message to the guest
    """
    try:
        await manager.send_message(
            websocket,
            WsMessageDto(
                message=WS_MESSAGES.SEND_ACTION,
                data={"action": action, "guest_id": guest_id},
            ),
        )
    except Exception as e:
        print(f"Error sending action {action} for guest {guest_id}: {e}")


async def keep_typing(guest_id: str, websocket: WebSocket):
    """
    Continuously sends typing_on indicator
    """
    try:
        while True:
            await send_action(guest_id, websocket, SENDER_ACTION["typing_on"])
            await asyncio.sleep(RESEND_TYPING_AFTER)
    except Exception as e:
        print(f"Error in keep_typing: {e}")


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
                guest = Guest(
                    id=guest_id,
                    provider=PROVIDERS.WEB,
                    account_name=random.choice(some_random_account_name),
                )
                guest_info = GuestInfo(guest_id=guest_id)
                await guest_repository.insert_guest(session, guest)
                await guest_info_repository.insert_guest_info(session, guest_info)
                await session.commit()
            return guest
        except Exception as e:
            await session.rollback()
            raise e


async def handle_test_chat(websocket: WebSocket, data: dict):
    typing_task = asyncio.create_task(keep_typing(data["id"], websocket))
    try:
        guest_id = data.get("id")
        await check_insert_guest(guest_id)
        await with_session(
            lambda session: chat_service.insert_chat(
                session,
                guest_id,
                CHAT_SIDES.CLIENT,
                data["message"],
                [],
                datetime.now(),
            )
        )
        message_parts: list[MessagePart] = await invoke_agent(guest_id, data["message"])
        if typing_task:
            typing_task.cancel()
        await send_action(guest_id, websocket, SENDER_ACTION["typing_off"])
        for part in message_parts:
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
            await with_session(
                lambda session: chat_service.insert_chat(
                    session,
                    guest_id,
                    CHAT_SIDES.STAFF,
                    response.get("text", ""),
                    response.get("attachments", []),
                    datetime.now(),
                )
            )
            guest = await with_session(
                lambda session: guest_repository.get_guest_by_id(session, guest_id)
            )
            await manager.send_message(
                websocket,
                WsMessageDto(
                    message=WS_MESSAGES.TEST_CHAT,
                    data=guest.to_dict(
                        include=["interests", "info", "last_chat_message"]
                    ),
                ),
            )
            await asyncio.sleep(0.5)
    except Exception as e:
        pass
    finally:
        if typing_task:
            typing_task.cancel()
