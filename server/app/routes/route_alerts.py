from app.configs.database import get_session
from app.services import alert_service
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response as HTTPResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def get_alerts(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get all alerts from the database.
    """
    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    type = request.query_params.get("type", "all")
    if type == "all":
        alerts = await alert_service.get_alerts(db, skip, limit)
        return alerts
    if type == "system":
        alerts = await alert_service.get_alert_by_type(db, "system", skip, limit)
        return alerts

    notification_id = request.query_params.get("notification", "all")
    if notification_id == "all":
        alerts = await alert_service.get_alert_by_type(db, "custom", skip, limit)
        return alerts
    alerts = await alert_service.get_alerts_by_notification_id(
        db, notification_id, skip, limit
    )
    return alerts


@router.patch("/{alert_id}")
async def update_alert_status(
    alert_id: str, request: Request, db: AsyncSession = Depends(get_session)
):
    """
    Update an alert in the database.
    """
    body = await request.json()
    status = body.get("status")
    if status is None:
        return HTTPResponse(status_code=400, content={"message": "status is required"})
    alert = await alert_service.update_alert_status(db, alert_id, status)
    return alert
