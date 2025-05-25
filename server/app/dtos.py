from typing import Any

from app.utils.agent_utils import dump_json
from pydantic import BaseModel


class ScriptChunkDto(BaseModel):
    script_id: str
    script_name: str
    chunk: str


class SheetChunkDto(BaseModel):
    sheet_id: str
    sheet_name: str
    chunk: str
    id: int


class PagingDto(BaseModel):
    skip: int
    limit: int
    data: list
    total: int
    has_next: bool = None
    has_prev: bool = None

    def __init__(self, **data):
        super().__init__(**data)
        self.has_next = self.skip + self.limit < self.total
        self.has_prev = self.skip > 0


class WsMessageDto(BaseModel):
    message: str
    data: Any = None

    def __str__(self):
        return dump_json(self.to_json())

    def to_json(self):
        return self.model_dump_json()


class PaginationDto(BaseModel):
    page: int
    limit: int
    total: int
    data: list
    has_next: bool = None
    has_prev: bool = None
    next_page: int = None
    prev_page: int = None
    total_pages: int = None

    def __init__(self, **data):
        super().__init__(**data)
        self.has_next = self.page * self.limit < self.total
        self.has_prev = self.page > 1
        self.next_page = self.page + 1 if self.has_next else None
        self.prev_page = self.page - 1 if self.has_prev else None
        self.total_pages = (self.total + self.limit - 1) // self.limit


class SheetColumnConfigDto(BaseModel):
    column_name: str
    column_type: str
    description: str = None
    is_index: bool = False

    def to_dict(self):
        return {
            "column_name": self.column_name,
            "column_type": self.column_type,
            "description": self.description,
            "is_index": self.is_index,
        }
