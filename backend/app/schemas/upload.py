from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RowError(BaseModel):
    row: int
    field: str
    message: str


class UploadResponse(BaseModel):
    upload_id: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[RowError]


class UploadStatus(BaseModel):
    upload_id: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    created_at: datetime
    processed_at: Optional[datetime]
