from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base_dtos import PaginationDto


class InterestBase(BaseModel):
    """Base schema for Interest"""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the interest"
    )
    color: str = Field(
        ...,
        min_length=1,
        max_length=7,
        description="Color code for the interest (hex format)",
    )
    related_terms: str = Field(..., description="Related terms for the interest")
    status: Literal["published", "draft"] = Field(
        "published", description="Status of the interest (published or draft)"
    )


class InterestCreate(InterestBase):
    """Schema for creating a new interest"""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Technology",
                "color": "#FF5733",
                "related_terms": "tech, programming, software development",
                "status": "published",
            }
        }


class InterestUpdate(BaseModel):
    """Schema for updating an existing interest"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Name of the interest"
    )
    color: Optional[str] = Field(
        None,
        min_length=1,
        max_length=7,
        description="Color code for the interest (hex format)",
    )
    related_terms: Optional[str] = Field(
        None, description="Related terms for the interest"
    )
    status: Optional[Literal["published", "draft"]] = Field(
        None, description="Status of the interest"
    )


class InterestResponse(InterestBase):
    """Schema for interest response"""

    id: str = Field(..., description="Unique identifier of the interest")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "interest-123",
                "name": "Technology",
                "color": "#FF5733",
                "description": "Interest in technology and programming",
                "status": "published",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }


class PaginatedInterestResponse(BaseModel):
    """Schema for paginated interest response"""

    items: List[InterestResponse] = Field(..., description="List of interests")
    pagination: PaginationDto = Field(..., description="Pagination information")


class InterestDeleteMultipleRequest(BaseModel):
    """Schema for deleting multiple interests"""

    interest_ids: List[str] = Field(
        ..., min_length=1, description="List of interest IDs to delete"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "interest_ids": ["interest-123", "interest-456", "interest-789"]
            }
        }


class InterestUploadSuccessResponse(BaseModel):
    """Schema for successful interest upload response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the upload")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Interest data uploaded successfully",
                "detail": "All interests from the Excel file have been processed and created.",
            }
        }


class InterestCreateSuccessResponse(BaseModel):
    """Schema for successful interest creation response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the creation")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Interest created successfully",
                "detail": "The new interest has been added to the database.",
            }
        }


class InterestDeleteResponse(BaseModel):
    """Schema for successful interest deletion response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the deletion")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Interest deleted successfully",
                "detail": "Interest with ID interest-123 has been removed from the database.",
            }
        }


class InterestDeleteMultipleResponse(BaseModel):
    """Schema for successful multiple interests deletion response"""

    message: str = Field(..., description="Success message")
    detail: str = Field(..., description="Detailed information about the deletion")
    deleted_count: int = Field(..., description="Number of interests deleted")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Interests deleted successfully",
                "detail": "Successfully deleted 3 interests from the database.",
                "deleted_count": 3,
            }
        }
