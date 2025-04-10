from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Guest
from app.dtos import PagingDto
from app.repositories import guest_repository, chat_repository


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
