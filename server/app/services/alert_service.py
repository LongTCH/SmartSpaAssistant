from app.configs.database import async_session
from app.dtos import PagingDto
from app.models import Alert
from app.repositories import alert_repository, notification_repository
from app.utils import string_utils
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


async def agent_insert_alert(notification_id: str, guest_id: str, **kwargs) -> str:
    """
    Insert a new alert into the database.
    """
    async with async_session() as session:
        notification = await notification_repository.get_notification_by_id(
            session, notification_id
        )
        template_str = notification.content
        alert_content = string_utils.render_tool_template(template_str, **kwargs)
        alert = Alert(
            notification_id=notification_id, content=alert_content, guest_id=guest_id
        )
        alert = await alert_repository.insert_alert(session, alert)
        await session.commit()
        return f"""
        Aleart {notification.label} has been sent with content:
        {alert.content}
        """
