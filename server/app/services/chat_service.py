from datetime import datetime

from app.models import Chat
from app.repositories import chat_repository, guest_repository
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_chat(
    db: AsyncSession,
    guest_id: str,
    side: str,
    text: str,
    attachments: list,
    created_at: datetime,
) -> Chat:
    """
    Insert a new chat message into the database.
    """
    message = {"text": text, "attachments": attachments}
    content = {"side": side, "message": message}
    chat = Chat(guest_id=guest_id, content=content, created_at=created_at)
    await chat_repository.insert_chat(db, chat)

    # update last message
    guest = await guest_repository.get_guest_by_id(db, guest_id)
    guest.last_message_id = chat.id
    await guest_repository.update_guest(db, guest)  # Thêm guest vào session

    await db.commit()
    await db.refresh(chat)
    return chat
