from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base_dtos import PaginationDto


class NotificationParam(BaseModel):
    """Schema for notification parameter"""

    index: int = Field(..., description="Parameter index (0-based)")
    param_name: str = Field(..., description="Parameter name")
    param_type: str = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")
    validation: Optional[str] = Field(None, description="Parameter validation rule")


class NotificationBase(BaseModel):
    """Base schema for Notification"""

    label: str = Field(
        ..., min_length=1, max_length=255, description="Label of the notification"
    )
    description: str = Field(
        ..., min_length=1, description="Description of the notification"
    )
    color: str = Field(
        "#000000",
        min_length=7,
        max_length=7,
        description="Color code for the notification (hex format)",
    )
    content: Optional[str] = Field(
        None, description="Template content with variable placeholders"
    )
    params: Optional[List[NotificationParam]] = Field(
        None, description="List of notification parameters"
    )
    status: Literal["published", "draft"] = Field(
        "published", description="Status of the notification (published or draft)"
    )


class NotificationCreate(NotificationBase):
    """Schema for creating a new notification"""

    class Config:
        json_schema_extra = {
            "example": {
                "label": "Order Notification",
                "description": "Notification for new orders",
                "color": "#2196F3",
                "content": "You have a new order from {{customer_name}} with total {{total}}",
                "params": [
                    {
                        "index": 0,
                        "param_name": "customer_name",
                        "param_type": "String",
                        "description": "Name of the customer",
                    },
                    {
                        "index": 1,
                        "param_name": "customer_phone",
                        "param_type": "Numeric",
                        "description": "Phone number of the customer",
                        "validation": "phone",
                    },
                    {
                        "index": 2,
                        "param_name": "total",
                        "param_type": "Numeric",
                        "description": "Total order value",
                    },
                ],
                "status": "published",
            }
        }


class NotificationUpdate(BaseModel):
    """Schema for updating an existing notification"""

    label: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Label of the notification"
    )
    description: Optional[str] = Field(
        None, min_length=1, description="Description of the notification"
    )
    color: Optional[str] = Field(
        None,
        min_length=7,
        max_length=7,
        description="Color code for the notification (hex format)",
    )
    content: Optional[str] = Field(
        None, description="Template content with variable placeholders"
    )
    params: Optional[List[NotificationParam]] = Field(
        None, description="List of notification parameters"
    )
    status: Optional[Literal["published", "draft"]] = Field(
        None, description="Status of the notification"
    )


class NotificationResponse(NotificationBase):
    """Schema for notification response"""

    id: str = Field(..., description="Unique identifier of the notification")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "notification-123",
                "label": "Order Notification",
                "description": "Notification for new orders",
                "color": "#2196F3",
                "content": "You have a new order from {{customer_name}} with total {{total}}",
                "params": [
                    {
                        "index": 0,
                        "param_name": "customer_name",
                        "param_type": "String",
                        "description": "Name of the customer",
                    }
                ],
                "status": "published",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }


class PaginatedNotificationResponse(BaseModel):
    """Schema for paginated notification response"""

    items: List[NotificationResponse] = Field(..., description="List of notifications")
    pagination: PaginationDto = Field(..., description="Pagination information")


class NotificationDeleteMultipleRequest(BaseModel):
    """Schema for deleting multiple notifications"""

    notification_ids: List[str] = Field(
        ..., min_length=1, description="List of notification IDs to delete"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "notification_ids": [
                    "notification-123",
                    "notification-456",
                    "notification-789",
                ]
            }
        }


class NotificationDeleteResponse(BaseModel):
    """Schema for notification deletion response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the deletion")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Notification deleted successfully",
                "detail": "Notification with ID notification-123 has been removed from the database.",
            }
        }


class NotificationDeleteMultipleResponse(BaseModel):
    """Schema for multiple notification deletion response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the deletion")
    deleted_count: int = Field(..., description="Number of notifications deleted")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Notifications deleted successfully",
                "detail": "Successfully deleted 3 notifications from the database.",
                "deleted_count": 3,
            }
        }


class NotificationUploadSuccessResponse(BaseModel):
    """Schema for successful notification upload response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the upload")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Notifications uploaded successfully",
                "detail": "All notifications from the Excel file have been processed and created.",
            }
        }


class NotificationCreateSuccessResponse(BaseModel):
    """Schema for successful notification creation response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the creation")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Notification created successfully",
                "detail": "The new notification has been added to the database.",
            }
        }
