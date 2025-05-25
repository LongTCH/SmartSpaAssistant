from app.configs.constants import WS_MESSAGES
from app.dtos import PagingDto, WsMessageDto
from app.models import Alert
from app.repositories import alert_repository
from app.services import connection_manager
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


async def get_alerts(db: AsyncSession, skip: int, limit: int) -> PagingDto:
    """
    Get a paginated list of alerts from the database.
    """
    count = await alert_repository.count_alerts(db)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    data = await alert_repository.get_paging_alerts(db, skip, limit)
    # Convert all objects to dictionaries
    data_dict = [alert.to_dict(include=["notification"]) for alert in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_alerts_by_notification_id(
    db: AsyncSession, notification_id: str, skip: int, limit: int
) -> PagingDto:
    """
    Get a paginated list of alerts from the database by notification_id.
    """
    count = await alert_repository.count_alerts_by_notification_id(db, notification_id)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    data = await alert_repository.get_paging_alerts_by_notification_id(
        db, skip, limit, notification_id
    )
    # Convert all objects to dictionaries
    data_dict = [alert.to_dict(include=["notification"]) for alert in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def update_alert_status(db: AsyncSession, alert_id: str, status: str) -> dict:
    """
    Update the status of an alert in the database.
    """
    alert = await alert_repository.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=404,
            detail=f"Alert with id {alert_id} not found",
        )
    alert.status = status
    alert = await alert_repository.update_alert(db, alert)
    return alert.to_dict(include=["notification"])


async def get_alert_by_type(
    db: AsyncSession, alert_type: str, skip: int, limit: int
) -> PagingDto:
    """
    Get a paginated list of alerts from the database by alert_type.
    """
    count = await alert_repository.count_alerts_by_type(db, alert_type)
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    data = await alert_repository.get_paging_alerts_by_type(db, skip, limit, alert_type)
    # Convert all objects to dictionaries
    data_dict = [alert.to_dict(include=["notification"]) for alert in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def get_alert_by_type_and_notification_id(
    db: AsyncSession, alert_type: str, notification_id: str, skip: int, limit: int
) -> PagingDto:
    """
    Get a paginated list of alerts from the database by alert_type and notification_id.
    """
    count = await alert_repository.count_alerts_by_type_and_notification_id(
        db, alert_type, notification_id
    )
    if count == 0:
        return PagingDto(skip=skip, limit=limit, total=0, data=[])
    data = await alert_repository.get_paging_alerts_by_type_and_notification_id(
        db, skip, limit, alert_type, notification_id
    )
    # Convert all objects to dictionaries
    data_dict = [alert.to_dict(include=["notification"]) for alert in data]
    return PagingDto(skip=skip, limit=limit, total=count, data=data_dict)


async def insert_system_alert(db: AsyncSession, guest_id: str, content: str) -> dict:
    """
    Insert a system alert into the database.
    """
    alert = Alert(
        guest_id=guest_id,
        type="system",
        status="unread",
        content=content,
    )
    alert = await alert_repository.insert_alert(db, alert)
    await db.commit()
    await notify_alert(db, alert.id)
    return alert.to_dict()


async def insert_custom_alert(
    db: AsyncSession, guest_id: str, notification_id: str, content: str
) -> dict:
    """
    Insert a custom alert into the database.
    """
    alert = Alert(
        guest_id=guest_id,
        type="custom",
        status="unread",
        content=content,
        notification_id=notification_id,
    )
    alert = await alert_repository.insert_alert(db, alert)
    await db.commit()
    await notify_alert(db, alert.id)
    return alert.to_dict()


async def notify_alert(db, alert_id: str) -> None:
    """
    Notify the alert to the connected clients.
    """
    alert = await alert_repository.get_alert_by_id(db, alert_id)
    if alert:
        await connection_manager.manager.broadcast(
            WsMessageDto(
                message=WS_MESSAGES.ALERT, data=alert.to_dict(include=["notification"])
            )
        )
