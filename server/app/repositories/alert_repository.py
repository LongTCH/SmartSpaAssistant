from app.models import Alert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


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
    stmt = (
        select(Alert)
        .options(selectinload(Alert.notification))
        .order_by(Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
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
        .options(selectinload(Alert.notification))
        .where(Alert.notification_id == notification_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def insert_alert(db: AsyncSession, alert: Alert) -> Alert:
    """
    Insert a new alert into the database.
    """
    db.add(alert)
    await db.flush()
    return alert


async def get_alert_by_id(db: AsyncSession, alert_id: str) -> Alert:
    """
    Get an alert by its ID from the database.
    """
    stmt = (
        select(Alert)
        .options(selectinload(Alert.notification))
        .where(Alert.id == alert_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def update_alert(db: AsyncSession, alert: Alert) -> Alert:
    """
    Update an alert in the database.
    """
    db.add(alert)
    await db.flush()
    return alert


async def count_alerts_by_type(db: AsyncSession, alert_type: str) -> int:
    """
    Count the number of alerts in the database by alert_type.
    """
    stmt = select(Alert).where(Alert.type == alert_type)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_alerts_by_type(
    db: AsyncSession, skip: int, limit: int, alert_type: str
) -> list[Alert]:
    """
    Get a paginated list of alerts from the database by alert_type.
    """
    stmt = (
        select(Alert)
        .options(selectinload(Alert.notification))
        .where(Alert.type == alert_type)
        .order_by(Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def count_alerts_by_type_and_notification_id(
    db: AsyncSession, alert_type: str, notification_id: str
) -> int:
    """
    Count the number of alerts in the database by alert_type and notification_id.
    """
    stmt = select(Alert).where(
        Alert.type == alert_type, Alert.notification_id == notification_id
    )
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_alerts_by_type_and_notification_id(
    db: AsyncSession, skip: int, limit: int, alert_type: str, notification_id: str
) -> list[Alert]:
    """
    Get a paginated list of alerts from the database by alert_type and notification_id.
    """
    stmt = (
        select(Alert)
        .options(selectinload(Alert.notification))
        .where(Alert.type == alert_type, Alert.notification_id == notification_id)
        .order_by(Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
