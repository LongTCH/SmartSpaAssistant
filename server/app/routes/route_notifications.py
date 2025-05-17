from app.configs.database import get_session
from app.services import notification_service
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response as HttpResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all notifications from the database.
    """
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    status = request.query_params.get("status", "all")
    if status == "all":
        notifications = await notification_service.get_notifications(db, page, limit)
        return notifications
    notifications = await notification_service.get_notifications_by_status(
        db, page, limit, status
    )
    return notifications


@router.get("/{id}")
async def get_notification_by_id(id: str, db: AsyncSession = Depends(get_session)):
    """
    Get a notification by its ID from the database.
    """
    notification = await notification_service.get_notification_by_id(db, id)
    return notification


@router.post("")
async def insert_notification(
    notification: dict, db: AsyncSession = Depends(get_session)
):
    """
    Insert a new notification into the database.
    """
    await notification_service.insert_notification(db, notification)
    return HttpResponse(status_code=201)


@router.put("/{id}")
async def update_notification(
    id: str, notification: dict, db: AsyncSession = Depends(get_session)
):
    """
    Update a notification in the database.
    """
    await notification_service.update_notification(db, id, notification)
    return HttpResponse(status_code=204)


@router.delete("/{id}")
async def delete_notification(id: str, db: AsyncSession = Depends(get_session)):
    """
    Delete a notification from the database by its ID.
    """
    await notification_service.delete_notification(db, id)
    return HttpResponse(status_code=204)


@router.post("/delete-multiple")
async def delete_multiple_notifications(
    request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Delete multiple notifications from the database by their IDs.
    """
    body = await request.json()
    notification_ids = body.get("notification_ids", [])
    await notification_service.delete_multiple_notifications(db, notification_ids)
    return HttpResponse(status_code=204)
