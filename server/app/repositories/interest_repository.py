from app.models import Interest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def count_interests(db: AsyncSession) -> int:
    stmt = select(Interest)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_interests_by_status(db: AsyncSession, status: str) -> int:
    stmt = select(Interest).where(Interest.status == status)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_interests(
    db: AsyncSession, skip: int, limit: int
) -> list[Interest]:
    stmt = (
        select(Interest).order_by(Interest.created_at.desc()).offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_paging_interests_by_status(
    db: AsyncSession, skip: int, limit: int, status: str
) -> list[Interest]:
    stmt = select(Interest).where(Interest.status == status).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_interest_by_id(db: AsyncSession, interest_id: str) -> Interest:
    stmt = select(Interest).where(Interest.id == interest_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_interest(db: AsyncSession, interest: Interest) -> Interest:
    db.add(interest)
    await db.flush()
    return interest


async def update_interest(db: AsyncSession, interest: Interest) -> Interest:
    db.add(interest)
    return interest


async def delete_interest(db: AsyncSession, interest_id: str) -> None:
    stmt = select(Interest).where(Interest.id == interest_id)
    result = await db.execute(stmt)
    interest = result.scalars().first()
    if interest:
        await db.delete(interest)
    return None


async def delete_multiple_interests(db: AsyncSession, interest_ids: list[str]) -> None:
    stmt = select(Interest).where(Interest.id.in_(interest_ids))
    result = await db.execute(stmt)
    interests = result.scalars().all()
    for interest in interests:
        await db.delete(interest)
    return None


async def get_all_interests(db: AsyncSession) -> list[Interest]:
    """
    Get all interests from the database.
    """
    stmt = select(Interest).order_by(Interest.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def insert_or_update_interests(
    db: AsyncSession, interests: list[Interest]
) -> None:
    """
    Insert or update multiple interests in the database.
    """
    db.add_all(interests)
    await db.flush()
    return None


async def get_interests_by_status(db: AsyncSession, status: str) -> list[Interest]:
    """
    Get all interests from the database.
    """
    stmt = (
        select(Interest)
        .where(Interest.status == status)
        .order_by(Interest.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
