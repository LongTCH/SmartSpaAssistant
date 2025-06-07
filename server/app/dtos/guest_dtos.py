from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base_dtos import PaginationDto


class GuestInfoDto(BaseModel):
    """Schema for guest information"""

    fullname: Optional[str] = Field(
        None,
        max_length=255,
        description="Full name of the guest",
        example="Nguyễn Văn A",
    )
    gender: Optional[Literal["male", "female", "other"]] = Field(
        None, description="Gender of the guest", example="male"
    )
    birthday: Optional[datetime] = Field(
        None, description="Birthday of the guest", example="1990-01-01T00:00:00Z"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Phone number of the guest",
        example="0987654321",
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Email address of the guest",
        example="nguyen.van.a@email.com",
    )
    address: Optional[str] = Field(
        None,
        description="Address of the guest",
        example="123 Đường ABC, Quận 1, TP.HCM",
    )


class GuestBase(BaseModel):
    """Base schema for Guest"""

    provider: Optional[str] = Field(
        None, description="Provider platform", example="facebook"
    )
    account_id: Optional[str] = Field(
        None, description="Account ID from provider", example="fb_123456789"
    )
    account_name: Optional[str] = Field(
        None, description="Account name from provider", example="Nguyễn Văn A"
    )
    avatar: Optional[str] = Field(
        None, description="Avatar URL", example="https://example.com/avatar.jpg"
    )
    assigned_to: Optional[str] = Field(
        "AI", description="Assigned to user or AI", example="AI"
    )


class GuestCreate(GuestBase):
    """Schema for creating a new guest"""

    info: Optional[GuestInfoDto] = Field(None, description="Guest information")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "facebook",
                "account_id": "fb_123456789",
                "account_name": "Nguyễn Văn A",
                "avatar": "https://example.com/avatar.jpg",
                "assigned_to": "AI",
                "info": {
                    "fullname": "Nguyễn Văn A",
                    "gender": "male",
                    "birthday": "1990-01-01T00:00:00Z",
                    "phone": "0987654321",
                    "email": "nguyen.van.a@email.com",
                    "address": "123 Đường ABC, Quận 1, TP.HCM",
                },
            }
        }


class GuestUpdate(BaseModel):
    """Schema for updating an existing guest"""

    fullname: Optional[str] = Field(
        None,
        max_length=255,
        description="Full name of the guest",
        example="Nguyễn Văn B",
    )
    gender: Optional[Literal["male", "female", "other"]] = Field(
        None, description="Gender of the guest", example="female"
    )
    birthday: Optional[str] = Field(
        None,
        description="Birthday of the guest (ISO format)",
        example="1992-05-15T00:00:00Z",
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Phone number of the guest",
        example="0123456789",
    )
    email: Optional[str] = Field(
        None,
        max_length=255,
        description="Email address of the guest",
        example="nguyen.van.b@email.com",
    )
    address: Optional[str] = Field(
        None,
        description="Address of the guest",
        example="456 Đường XYZ, Quận 2, TP.HCM",
    )
    interest_ids: Optional[List[str]] = Field(
        None,
        description="List of interest IDs",
        example=["interest-123", "interest-456"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "fullname": "Nguyễn Văn B",
                "gender": "female",
                "birthday": "1992-05-15T00:00:00Z",
                "phone": "0123456789",
                "email": "nguyen.van.b@email.com",
                "address": "456 Đường XYZ, Quận 2, TP.HCM",
                "interest_ids": ["interest-123", "interest-456"],
            }
        }


class GuestResponse(GuestBase):
    """Schema for guest response"""

    id: str = Field(
        ..., description="Unique identifier of the guest", example="guest-123"
    )
    created_at: datetime = Field(
        ..., description="Creation timestamp", example="2024-01-01T00:00:00Z"
    )
    updated_at: datetime = Field(
        ..., description="Last update timestamp", example="2024-01-01T12:30:00Z"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "guest-123",
                "provider": "facebook",
                "account_id": "fb_123456789",
                "account_name": "Nguyễn Văn A",
                "avatar": "https://example.com/avatar.jpg",
                "assigned_to": "AI",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T12:30:00Z",
            }
        }


class AssignmentUpdate(BaseModel):
    """Schema for updating guest assignment"""

    assigned_to: str = Field(
        ..., description="Assign guest to user or AI", example="user123"
    )

    class Config:
        json_schema_extra = {"example": {"assigned_to": "user123"}}


class GuestInterestUpdate(BaseModel):
    """Schema for updating guest interests"""

    interest_ids: List[str] = Field(
        ...,
        description="List of interest IDs",
        example=["interest-123", "interest-456"],
    )

    class Config:
        json_schema_extra = {
            "example": {"interest_ids": ["interest-123", "interest-456"]}
        }


class GuestFilterRequest(BaseModel):
    """Schema for filtering guests"""

    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Number of items per page")
    keyword: Optional[str] = Field(None, description="Keyword to search in guest data")
    interest_ids: Optional[List[str]] = Field(
        None, description="List of interest IDs to filter by"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "limit": 10,
                "keyword": "John",
                "interest_ids": ["interest-123", "interest-456"],
            }
        }


class PaginatedGuestResponse(BaseModel):
    """Schema for paginated guest response"""

    items: List[GuestResponse] = Field(..., description="List of guests")
    pagination: PaginationDto = Field(..., description="Pagination information")


class GuestDeleteMultipleRequest(BaseModel):
    """Schema for deleting multiple guests"""

    guest_ids: List[str] = Field(
        ..., min_length=1, description="List of guest IDs to delete"
    )

    class Config:
        json_schema_extra = {
            "example": {"guest_ids": ["guest-123", "guest-456", "guest-789"]}
        }


class GuestDeleteResponse(BaseModel):
    """Schema for guest deletion response"""

    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {"example": {"message": "Guest deleted successfully"}}


class GuestDeleteMultipleResponse(BaseModel):
    """Schema for multiple guest deletion response"""

    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {"example": {"message": "Guests deleted successfully"}}
