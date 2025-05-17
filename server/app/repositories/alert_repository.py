from app.models import Alert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def count_alerts(db: AsyncSession) -> int:
    """
    Count the total number of alerts in the database.
    """
    stmt = select(Alert)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_alerts(db: AsyncSession, skip: int, limit: int) -> list[Alert]:
    """
    Get a paginated list of alerts from the database.
    """
    stmt = select(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def count_alerts_by_notification_id(
    db: AsyncSession, notification_id: str
) -> int:
    """
    Count the number of alerts in the database by notification_id.
    """
    stmt = select(Alert).where(Alert.notification_id == notification_id)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_alerts_by_notification_id(
    db: AsyncSession, skip: int, limit: int, notification_id: str
) -> list[Alert]:
    """
    Get a paginated list of alerts from the database by notification_id.
    """
    stmt = (
        select(Alert)
        .where(Alert.notification_id == notification_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
