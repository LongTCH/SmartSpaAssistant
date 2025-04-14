from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Guest, Chat
from app.dtos import PagingDto
from app.repositories import guest_repository, chat_repository
from datetime import datetime


async def get_conversations(db: AsyncSession,  skip: int, limit: int) -> PagingDto:
    count = await guest_repository.count_guests(db)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await guest_repository.get_paging_conversation(db, skip, limit)
    return PagingDto(skip=skip, limit=limit, total=count, data=data)


async def get_chat_by_guest_id(db: AsyncSession, guest_id: str, skip: int, limit: int) -> PagingDto:
    count = await chat_repository.count_chat_by_guest_id(db, guest_id)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await chat_repository.get_chat_by_guest_id(db, guest_id, skip, limit)
    return PagingDto(skip=skip, limit=limit, total=count, data=data)


async def get_conversation_by_provider(db: AsyncSession, provider: str, account_id: str) -> Guest:
    return await guest_repository.get_conversation_by_provider(db, provider, account_id)


async def insert_chat(db: AsyncSession, guest_id: str, side: str, text: str, attachments: list, created_at: datetime) -> Chat:
    message = {
        "text": text,
        "attachments": attachments
    }
    content = {
        "side": side,
        "message": message
    }
    chat = Chat(guest_id=guest_id, content=content, created_at=created_at)
    return await chat_repository.insert_chat(db, chat)


async def insert_guest(db: AsyncSession, guest: Guest) -> Guest:
    return await guest_repository.insert_guest(db, guest)


async def update_last_message(db: AsyncSession, guest_id: str, chat: Chat) -> Guest:
    return await guest_repository.update_last_message(db, guest_id, chat.content, chat.created_at)
