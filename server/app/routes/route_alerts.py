from app.configs.database import get_session
from app.services import alert_service
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def get_alerts(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all alerts from the database.
    """
    skip = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    notification_id = request.query_params.get("notification_id", "all")
    if notification_id == "all":
        alerts = await alert_service.get_alerts(db, skip, limit)
        return alerts
    alerts = await alert_service.get_alerts_by_notification_id(
        db, notification_id, skip, limit
    )
    return alerts
