from datetime import datetime

from app.dtos import PaginationDto
from app.models import Notification
from app.repositories import notification_repository
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified


async def get_notifications(db: AsyncSession, page: int, limit: int) -> PaginationDto:
    """
    Get a paginated list of notifications from the database.
    """
    count = await notification_repository.count_notifications(db)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await notification_repository.get_paging_notifications(db, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [notification.to_dict() for notification in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_notifications_by_status(
    db: AsyncSession, page: int, limit: int, status: str
) -> PaginationDto:
    """
    Get a paginated list of notifications from the database.
    """
    count = await notification_repository.count_notifications_by_status(db, status)
    if count == 0:
        return PaginationDto(page=page, limit=limit, total=0, data=[])
    skip = (page - 1) * limit
    data = await notification_repository.get_paging_notifications_by_status(
        db, skip, limit, status
    )
    # Convert all objects to dictionaries
    data_dict = [notification.to_dict() for notification in data]
    return PaginationDto(page=page, limit=limit, total=count, data=data_dict)


async def get_notification_by_id(db: AsyncSession, notification_id: str) -> dict:
    """
    Get a notification by its ID from the database.
    """
    notification = await notification_repository.get_notification_by_id(
        db, notification_id
    )
    return notification.to_dict() if notification else None


async def insert_notification(db: AsyncSession, notification: dict) -> None:
    """
    Insert a new notification into the database.
    """
    try:
        notification_obj = Notification(
            label=notification.get("label"),
            status=notification.get("status"),
            color=notification.get("color"),
            description=notification.get("description"),
            params=notification.get("params"),
            content=notification.get("content"),
            created_at=datetime.now(),
        )
        await notification_repository.insert_notification(db, notification_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def update_notification(
    db: AsyncSession, notification_id: str, notification: dict
) -> None:
    """
    Update an existing notification in the database.
    """
    try:
        notification_obj = await notification_repository.get_notification_by_id(
            db, notification_id
        )
        if not notification_obj:
            raise HTTPException(status_code=404, detail="Notification not found")
        notification_obj.label = notification.get("label")
        notification_obj.status = notification.get("status")
        notification_obj.color = notification.get("color")
        notification_obj.description = notification.get("description")
        notification_obj.params = notification.get("params")
        notification_obj.content = notification.get("content")
        flag_modified(notification_obj, "params")
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_notification(db: AsyncSession, notification_id: str) -> None:
    """
    Delete a notification from the database by its ID.
    """
    try:
        await notification_repository.delete_notification(db, notification_id)
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_multiple_notifications(
    db: AsyncSession, notification_ids: list
) -> None:
    """
    Delete multiple notifications from the database by their IDs.
    """
    try:
        await notification_repository.delete_multiple_notifications(
            db, notification_ids
        )
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
