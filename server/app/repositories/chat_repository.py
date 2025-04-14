from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Chat
from sqlalchemy.future import select


async def count_chat_by_guest_id(db: AsyncSession, guest_id: str) -> int:
    stmt = select(Chat).where(Chat.guest_id == guest_id)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_chat_by_guest_id(db: AsyncSession, guest_id: str, skip: int, limit: int) -> list[Chat]:
    stmt = select(Chat).where(Chat.guest_id == guest_id).order_by(
        Chat.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def insert_chat(db: AsyncSession, chat: Chat) -> Chat:
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat
