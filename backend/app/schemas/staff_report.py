import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class StaffReportCreate(BaseModel):
    description: str = Field(..., max_length=2000)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class StaffReportResponse(StaffReportCreate):
    id: uuid.UUID
    photo_url: Optional[str] = None
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True
