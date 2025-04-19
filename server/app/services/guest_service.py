from app.dtos import PagingDto
from app.models import Guest
from app.repositories import chat_repository, guest_repository
from sqlalchemy.ext.asyncio import AsyncSession


async def get_conversations(db: AsyncSession, skip: int, limit: int) -> PagingDto:
    count = await guest_repository.count_guests(db)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await guest_repository.get_paging_conversation(db, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [guest.to_dict() for guest in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_conversations_by_assignment(
    db: AsyncSession, assigned_to: str, skip: int, limit: int
) -> PagingDto:
    count = await guest_repository.count_guests_by_assignment(db, assigned_to)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await guest_repository.get_paging_conversation_by_assignment(
        db, assigned_to, skip, limit
    )
    # Convert all objects to dictionaries
    data_dict = [guest.to_dict() for guest in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_chat_by_guest_id(
    db: AsyncSession, guest_id: str, skip: int, limit: int
) -> PagingDto:
    count = await chat_repository.count_chat_by_guest_id(db, guest_id)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await chat_repository.get_chat_by_guest_id(db, guest_id, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [chat.to_dict() for chat in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_conversation_by_provider(
    db: AsyncSession, provider: str, account_id: str
) -> dict:
    guest = await guest_repository.get_conversation_by_provider(
        db, provider, account_id
    )
    return guest.to_dict() if guest else None


async def insert_guest(db: AsyncSession, guest: Guest) -> dict:
    guest = await guest_repository.insert_guest(db, guest)
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict()


async def get_paging_guests_by_sentiment(
    db: AsyncSession, sentiment: str, skip: int, limit: int
) -> PagingDto:
    count = await guest_repository.count_guests_by_sentiment(db, sentiment)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    if skip >= count:
        return PagingDto(skip=skip, limit=limit, total=count, data=[])
    data = await guest_repository.get_guests_by_sentiment(db, sentiment, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [guest.to_dict() for guest in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def update_assignment(db: AsyncSession, guest_id: str, assigned_to: str) -> dict:
    guest = await guest_repository.update_assignment(db, guest_id, assigned_to)
    await db.commit()
    await db.refresh(guest)
    return guest.to_dict()
