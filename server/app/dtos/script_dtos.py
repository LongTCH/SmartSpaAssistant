from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base_dtos import PaginationDto  # Import from base_dtos


class ScriptChunkDto(BaseModel):
    script_id: str
    script_name: str
    chunk: str


class ScriptBase(BaseModel):
    name: str = Field(..., min_length=1, example="Greeting Script")
    description: str = Field(..., example="A script to greet users.")
    solution: str = Field(..., example="Hello, welcome!")
    status: Literal["published", "draft"] = Field("published", example="published")


class ScriptCreate(ScriptBase):
    related_script_ids: Optional[List[str]] = Field(default=[], example=["id1", "id2"])


class ScriptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, example="Updated Greeting Script")
    description: Optional[str] = Field(
        None, example="An updated script to greet users."
    )
    solution: Optional[str] = Field(None, example="Hi there, welcome!")
    status: Optional[Literal["published", "draft"]] = Field(None, example="draft")
    related_script_ids: Optional[List[str]] = Field(None, example=["id1", "id2"])


class ScriptResponse(ScriptBase):
    id: str = Field(..., example="c3a2b1f0-0000-0000-0000-000000000000")
    created_at: datetime = Field(..., example="2025-06-07T12:00:00Z")

    class Config:
        from_attributes = True


class PaginatedScriptResponse(PaginationDto):
    data: List[ScriptResponse]


class ScriptDeleteMultipleRequest(BaseModel):
    script_ids: List[str] = Field(..., example=["id1", "id2"])


class UploadSuccessResponse(BaseModel):
    message: str = Field(default="Scripts uploaded successfully.")
    script_ids: List[str]
