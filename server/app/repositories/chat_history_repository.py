from app.models import ChatHistory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_chat_history(
    db: AsyncSession, guest_id: str, content: str, summary: str
) -> ChatHistory:
    chat_history = ChatHistory(guest_id=guest_id, content=content, summary=summary)
    db.add(chat_history)
    await db.flush()
    return chat_history


async def get_latest_chat_histories(
    db: AsyncSession, guest_id: str, limit: int = 5
) -> list[ChatHistory]:
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.guest_id == guest_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_long_term_memory(
    db: AsyncSession, guest_id: str, skip: int, limit=50
) -> list[ChatHistory]:
    # get column 'summary' sorted by 'created_at' in descending order with limit
    stmt = (
        select(ChatHistory.summary)
        .where(ChatHistory.guest_id == guest_id)
        .order_by(ChatHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
