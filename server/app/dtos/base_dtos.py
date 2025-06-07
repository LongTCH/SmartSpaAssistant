from typing import Any, Optional

# Assuming this is still needed for WsMessageDto if it's moved here
from app.utils.agent_utils import dump_json
from fastapi import status
from pydantic import BaseModel, Field


class PagingDto(BaseModel):
    skip: int = Field(..., description="Number of items to skip", example=0)
    limit: int = Field(..., description="Maximum number of items to return", example=10)
    data: list = Field(..., description="Array of items", example=[])
    total: int = Field(..., description="Total number of items available", example=100)
    has_next: Optional[bool] = Field(
        None,
        description="Whether there are more items after current page",
        example=True,
    )
    has_prev: Optional[bool] = Field(
        None, description="Whether there are items before current page", example=False
    )

    def __init__(self, **data):
        super().__init__(**data)
        self.has_next = self.skip + self.limit < self.total
        self.has_prev = self.skip > 0

    class Config:
        json_schema_extra = {
            "example": {
                "skip": 0,
                "limit": 10,
                "data": [],
                "total": 100,
                "has_next": True,
                "has_prev": False,
            }
        }


class WsMessageDto(BaseModel):
    message: str
    data: Any = None

    def __str__(self):
        # Ensure dump_json is available or remove if not used
        return dump_json(self.to_json())

    def to_json(self):
        return self.model_dump_json()


class PaginationDto(BaseModel):
    page: int = Field(..., description="Current page number", example=1)
    limit: int = Field(..., description="Number of items per page", example=10)
    total: int = Field(..., description="Total number of items", example=100)
    data: list = Field(..., description="Array of items for current page")
    has_next: Optional[bool] = Field(
        None, description="Whether there are more pages", example=True
    )
    has_prev: Optional[bool] = Field(
        None, description="Whether there are previous pages", example=False
    )
    next_page: Optional[int] = Field(None, description="Next page number", example=2)
    prev_page: Optional[int] = Field(
        None, description="Previous page number", example=None
    )
    total_pages: Optional[int] = Field(
        None, description="Total number of pages", example=10
    )

    def __init__(self, **data):
        super().__init__(**data)
        self.has_next = self.page * self.limit < self.total
        self.has_prev = self.page > 1
        self.next_page = self.page + 1 if self.has_next else None
        self.prev_page = self.page - 1 if self.has_prev else None
        self.total_pages = (self.total + self.limit - 1) // self.limit

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "limit": 10,
                "total": 100,
                "data": [],
                "has_next": True,
                "has_prev": False,
                "next_page": 2,
                "prev_page": None,
                "total_pages": 10,
            }
        }


class ErrorDetail(BaseModel):
    detail: str = Field(..., description="Error message describing what went wrong")

    class Config:
        json_schema_extra = {"example": {"detail": "Resource not found"}}


common_error_responses = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorDetail,
        "description": "Bad Request - Invalid input data",
        "content": {
            "application/json": {"example": {"detail": "Invalid request data"}}
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorDetail,
        "description": "Resource Not Found",
        "content": {"application/json": {"example": {"detail": "Resource not found"}}},
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "model": ErrorDetail,
        "description": "Validation Error - Input data validation failed",
        "content": {
            "application/json": {
                "example": {"detail": "Validation error: field is required"}
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorDetail,
        "description": "Internal Server Error - Something went wrong on the server",
        "content": {
            "application/json": {"example": {"detail": "Internal server error"}}
        },
    },
}
