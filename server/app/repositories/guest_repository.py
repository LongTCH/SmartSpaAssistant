from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models import Guest
from sqlalchemy.future import select


async def count_guests(db: AsyncSession) -> int:
    stmt = select(Guest)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_guests(db: AsyncSession, skip: int, limit: int) -> list[Guest]:
    stmt = select(Guest).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_paging_conversation(db: AsyncSession, skip: int, limit: int) -> list[Guest]:
    stmt = select(Guest).order_by(Guest.last_message_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()