from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail for consistent error responses"""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Consistent error response envelope"""

    ok: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    """Consistent success response envelope"""

    ok: bool = True
    data: T


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)

    @field_validator("title", "content")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v


class NoteRead(BaseModel):
    id: int
    title: str
    content: str

    class Config:
        from_attributes = True


class ActionItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)

    @field_validator("description")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v


class ActionItemRead(BaseModel):
    id: int
    description: str
    completed: bool

    class Config:
        from_attributes = True


class ExtractionResultSchema(BaseModel):
    """Schema for extraction results from note content"""

    hashtags: list[str]
    action_items: list[str]


class ExtractedData(BaseModel):
    """Schema for persisted extraction data"""

    action_items_created: list[ActionItemRead]
    tags_found: list[str]
