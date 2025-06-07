from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base_dtos import PaginationDto


class SheetChunkDto(BaseModel):
    sheet_id: str
    sheet_name: str
    chunk: str
    id: int


class SheetColumnConfigDto(BaseModel):
    column_name: str
    column_type: str
    description: str = None
    is_index: bool = Field(..., description="Whether this column is an index column")

    def to_dict(self):
        return {
            "column_name": self.column_name,
            "column_type": self.column_type,
            "description": self.description,
            "is_index": self.is_index,
        }


class SheetColumnConfigCreate(BaseModel):
    """Schema for creating sheet column configuration"""

    column_name: str = Field(..., description="Name of the column")
    column_type: str = Field(
        ..., description="Type of the column (e.g., 'string', 'number', 'date')"
    )
    description: Optional[str] = Field(None, description="Description of the column")
    is_index: bool = Field(..., description="Whether this column is an index column")


class SheetBase(BaseModel):
    """Base schema for Sheet"""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the sheet"
    )
    description: str = Field(..., min_length=1, description="Description of the sheet")
    status: Literal["published", "draft"] = Field(
        "published", description="Status of the sheet (published or draft)"
    )


class SheetCreate(SheetBase):
    """Schema for creating a new sheet"""

    column_config: Optional[List[SheetColumnConfigCreate]] = Field(
        None, description="Column configuration for the sheet"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customer Data",
                "description": "Database containing customer information",
                "status": "published",
                "column_config": [
                    {
                        "column_name": "customer_id",
                        "column_type": "string",
                        "description": "Unique customer identifier",
                        "is_index": True,
                    },
                    {
                        "column_name": "customer_name",
                        "column_type": "string",
                        "description": "Full name of the customer",
                    },
                ],
            }
        }


class SheetUpdate(BaseModel):
    """Schema for updating an existing sheet"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Name of the sheet"
    )
    description: Optional[str] = Field(
        None, min_length=1, description="Description of the sheet"
    )
    status: Optional[Literal["published", "draft"]] = Field(
        None, description="Status of the sheet"
    )
    column_config: Optional[List[SheetColumnConfigCreate]] = Field(
        None, description="Column configuration for the sheet"
    )


class SheetResponse(SheetBase):
    """Schema for sheet response"""

    id: str = Field(..., description="Unique identifier of the sheet")
    column_config: Optional[List[dict]] = Field(
        None, description="Column configuration"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "sheet-123",
                "name": "Customer Data",
                "description": "Database containing customer information",
                "status": "published",
                "column_config": [
                    {
                        "column_name": "customer_id",
                        "column_type": "string",
                        "description": "Unique customer identifier",
                        "is_index": True,
                    }
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }


class PaginatedSheetResponse(BaseModel):
    """Schema for paginated sheet response"""

    items: List[SheetResponse] = Field(..., description="List of sheets")
    pagination: PaginationDto = Field(..., description="Pagination information")


class SheetDeleteMultipleRequest(BaseModel):
    """Schema for deleting multiple sheets"""

    sheet_ids: List[str] = Field(
        ..., min_length=1, description="List of sheet IDs to delete"
    )

    class Config:
        json_schema_extra = {
            "example": {"sheet_ids": ["sheet-123", "sheet-456", "sheet-789"]}
        }


class SheetRowResponse(BaseModel):
    """Schema for sheet row response"""

    items: List[dict] = Field(..., description="List of sheet rows")
    pagination: PaginationDto = Field(..., description="Pagination information")


class SheetUploadSuccessResponse(BaseModel):
    """Schema for successful sheet upload response"""

    message: str = Field(..., description="Success message")
    sheet_id: str = Field(..., description="ID of the created sheet")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Sheet uploaded successfully.",
                "sheet_id": "sheet-123",
            }
        }
