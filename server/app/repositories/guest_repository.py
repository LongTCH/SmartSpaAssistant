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
    stmt = select(Guest).order_by(
        Guest.last_message_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_conversation_by_provider(db: AsyncSession, provider: str, account_id: str) -> Guest:
    stmt = select(Guest).where(Guest.provider == provider,
                               Guest.account_id == account_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_guest(db: AsyncSession, guest: Guest) -> Guest:
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest


async def update_last_message(db: AsyncSession, guest_id: str, last_message, last_message_at) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.last_message_at = last_message_at
        guest.last_message = last_message
        await db.commit()
        await db.refresh(guest)
        return guest
    return None
