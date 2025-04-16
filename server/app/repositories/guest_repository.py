from app.models import Guest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def count_guests(db: AsyncSession) -> int:
    stmt = select(Guest)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_guests_by_assignment(db: AsyncSession, assigned_to: str) -> int:
    stmt = select(Guest).where(Guest.assigned_to == assigned_to)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_guests(db: AsyncSession, skip: int, limit: int) -> list[Guest]:
    stmt = select(Guest).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_paging_conversation(
    db: AsyncSession, skip: int, limit: int
) -> list[Guest]:
    stmt = (
        select(Guest).order_by(Guest.last_message_at.desc()).offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_paging_conversation_by_assignment(
    db: AsyncSession, assigned_to: str, skip: int, limit: int
) -> list[Guest]:
    stmt = (
        select(Guest)
        .where(Guest.assigned_to == assigned_to)
        .order_by(Guest.last_message_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_conversation_by_provider(
    db: AsyncSession, provider: str, account_id: str
) -> Guest:
    stmt = select(Guest).where(
        Guest.provider == provider, Guest.account_id == account_id
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_guest(db: AsyncSession, guest: Guest) -> Guest:
    db.add(guest)
    return guest


async def update_last_message(
    db: AsyncSession, guest_id: str, last_message, last_message_at
) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.last_message_at = last_message_at
        guest.last_message = last_message
        return guest
    return None


async def update_sentiment(db: AsyncSession, guest_id: str, sentiment: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.sentiment = sentiment
        return guest
    return None


async def increase_message_count(db: AsyncSession, guest_id: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.message_count += 1
        return guest
    return None


async def reset_message_count(db: AsyncSession, guest_id: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.message_count = 0
        return guest
    return None


async def count_guests_by_sentiment(db: AsyncSession, sentiment: str) -> int:
    stmt = select(Guest).where(Guest.sentiment == sentiment)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_guests_by_sentiment(
    db: AsyncSession, sentiment: str, skip: int, limit: int
) -> list[Guest]:
    stmt = (
        select(Guest)
        .where(Guest.sentiment == sentiment)
        .order_by(Guest.last_message_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_assignment(db: AsyncSession, guest_id: str, assigned_to: str) -> Guest:
    stmt = select(Guest).where(Guest.id == guest_id)
    result = await db.execute(stmt)
    guest = result.scalars().first()
    if guest:
        guest.assigned_to = assigned_to
        return guest
    return None
