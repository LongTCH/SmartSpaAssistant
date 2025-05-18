from app.models import Notification
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def count_notifications(db: AsyncSession) -> int:
    stmt = select(Notification)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def count_notifications_by_status(db: AsyncSession, status: str) -> int:
    stmt = select(Notification).where(Notification.status == status)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def get_paging_notifications(
    db: AsyncSession, skip: int, limit: int
) -> list[Notification]:
    stmt = (
        select(Notification)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_paging_notifications_by_status(
    db: AsyncSession, skip: int, limit: int, status: str
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.status == status)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_notification_by_id(
    db: AsyncSession, notification_id: str
) -> Notification:
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def insert_notification(
    db: AsyncSession, notification: Notification
) -> Notification:
    db.add(notification)
    await db.flush()
    return notification


async def update_notification(
    db: AsyncSession, notification: Notification
) -> Notification:
    db.add(notification)
    return notification


async def delete_notification(db: AsyncSession, notification_id: str) -> None:
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    notification = result.scalars().first()
    if notification:
        await db.delete(notification)
    return None


async def delete_multiple_notifications(
    db: AsyncSession, notification_ids: list[str]
) -> None:
    stmt = select(Notification).where(Notification.id.in_(notification_ids))
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    for notification in notifications:
        await db.delete(notification)
    return None


async def get_all_notifications(db: AsyncSession) -> list[Notification]:
    stmt = select(Notification)
    result = await db.execute(stmt)
    return result.scalars().all()
