from app.dtos import PagingDto
from app.repositories import alert_repository
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
