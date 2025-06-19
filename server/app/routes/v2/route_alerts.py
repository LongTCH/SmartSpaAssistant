from typing import Optional

from app.configs.database import get_session
from app.services import alert_service
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v2/alerts", tags=["Alerts"])


class AlertResponse(BaseModel):
    """Alert response model"""

    id: str = Field(..., description="Unique identifier for the alert")
    guest_id: Optional[str] = Field(
        None, description="ID of the guest who triggered the alert"
    )
    type: str = Field(..., description="Type of alert (system or custom)")
    content: str = Field(..., description="Alert content/message")
    status: str = Field(..., description="Alert status (read or unread)")
    created_at: str = Field(..., description="Alert creation timestamp")
    notification_id: Optional[str] = Field(
        None, description="ID of the associated notification template"
    )
    notification: Optional[dict] = Field(
        None, description="Associated notification details"
    )

    class Config:
        from_attributes = True


class AlertStatusUpdate(BaseModel):
    """Request model for updating alert status"""

    status: str = Field(..., description="New status for the alert (read or unread)")


@router.get(
    "",
    summary="Get alerts",
    description="""
    Retrieve alerts with filtering and pagination options.
    
    **Filter Options:**
    - **type=all**: Get all alerts (default)
    - **type=system**: Get only system alerts
    - **type=custom**: Get only custom alerts
    - **notification**: Filter custom alerts by notification ID
    
    **Pagination:**
    - Use skip and limit parameters for pagination
    """,
    responses={
        200: {
            "description": "List of alerts retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "skip": 0,
                        "limit": 20,
                        "data": [
                            {
                                "id": "1fda3ad2-043a-4b9a-befd-ca730ecb3f48",
                                "guest_id": "8fde9e3b-25f5-4e54-b575-62c86fd122a6",
                                "type": "custom",
                                "status": "unread",
                                "content": "Bạn có lịch hẹn:\nKhách: Trương Long\nSĐT: 0987654311\nMuốn đến cơ sở 97-99 Đ Nguyễn Văn Linh, Phường Nam Dương, Hải Châu, Đà Nẵng , Việt Nam\nVào lúc 2025-06-06 08:00:00",
                                "created_at": "2025-06-05T05:35:56.720474",
                                "notification_id": "339b8b1a-37be-4bef-a453-32ad97dd2c73",
                                "notification": {
                                    "id": "339b8b1a-37be-4bef-a453-32ad97dd2c73",
                                    "label": "đặt lịch",
                                    "status": "published",
                                    "color": "#2196F3",
                                    "description": "Khi khách muốn đặt hẹn đến trực tiếp các cơ sở của Mailisa.",
                                    "content": "Bạn có lịch hẹn:\nKhách: {{ customer_name }}\nSĐT: {{ customer_phone }}\nMuốn đến cơ sở {{ spa_address }}\nVào lúc {{ time }}",
                                    "created_at": "2025-06-05T04:51:40.057050",
                                },
                            }
                        ],
                        "total": 1,
                        "has_next": False,
                        "has_prev": False,
                    }
                }
            },
        }
    },
)
async def get_alerts(
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of alerts to return"
    ),
    type: str = Query(
        "all", description="Filter by alert type: all, system, or custom"
    ),
    notification: str = Query(
        "all", description="Filter custom alerts by notification ID"
    ),
    db: AsyncSession = Depends(get_session),
):
    """
    Get all alerts from the database with filtering and pagination.
    """
    if type == "all":
        alerts = await alert_service.get_alerts(db, skip, limit)
        return alerts.model_dump()
    if type == "system":
        alerts = await alert_service.get_alert_by_type(db, "system", skip, limit)
        return alerts.model_dump()

    if notification == "all":
        alerts = await alert_service.get_alert_by_type(db, "custom", skip, limit)
        return alerts.model_dump()
    alerts = await alert_service.get_alerts_by_notification_id(
        db, notification, skip, limit
    )
    return alerts.model_dump()


@router.patch(
    "/{alert_id}",
    summary="Update alert status",
    description="""
    Update the status of a specific alert.
    
    **Common Use Cases:**
    - Mark an alert as read
    - Mark an alert as unread
    
    **Status Values:**
    - "read" - Alert has been viewed
    - "unread" - Alert has not been viewed
    """,
    responses={
        200: {
            "description": "Alert status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "1fda3ad2-043a-4b9a-befd-ca730ecb3f48",
                        "guest_id": "8fde9e3b-25f5-4e54-b575-62c86fd122a6",
                        "type": "custom",
                        "status": "read",
                        "content": "Bạn có lịch hẹn:\nKhách: Trương Long\nSĐT: 0987654311\nMuốn đến cơ sở 97-99 Đ Nguyễn Văn Linh, Phường Nam Dương, Hải Châu, Đà Nẵng , Việt Nam\nVào lúc 2025-06-06 08:00:00",
                        "created_at": "2025-06-05T05:35:56.720474",
                        "notification_id": "339b8b1a-37be-4bef-a453-32ad97dd2c73",
                        "notification": {
                            "id": "339b8b1a-37be-4bef-a453-32ad97dd2c73",
                            "label": "đặt lịch",
                            "status": "published",
                            "color": "#2196F3",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Bad request - missing or invalid status",
            "content": {
                "application/json": {"example": {"detail": "status is required"}}
            },
        },
        404: {
            "description": "Alert not found",
            "content": {"application/json": {"example": {"detail": "Alert not found"}}},
        },
    },
)
async def update_alert_status(
    request_body: AlertStatusUpdate,
    alert_id: str = Path(..., description="ID of the alert to update"),
    db: AsyncSession = Depends(get_session),
):
    """
    Update an alert status in the database.
    """
    if request_body.status not in ["read", "unread"]:
        raise HTTPException(status_code=400, detail="Status must be 'read' or 'unread'")

    alert = await alert_service.update_alert_status(db, alert_id, request_body.status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert
