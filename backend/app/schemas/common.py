from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    page: int
    page_size: int
    total: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[str] = None
