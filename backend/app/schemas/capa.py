import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.audit import RiskLevelEnum
from app.models.capa import CapaStatusEnum, NotifyChannelEnum

# Capa Evidence Schemas
class CapaEvidenceBase(BaseModel):
    file_url: str = Field(..., max_length=1000)
    mime_type: Optional[str] = Field(None, max_length=100)

class CapaEvidenceCreate(CapaEvidenceBase):
    pass

class CapaEvidenceResponse(CapaEvidenceBase):
    id: uuid.UUID
    capa_id: uuid.UUID
    uploaded_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Capa Schemas
class CapaBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    deadline: date
    priority: RiskLevelEnum = RiskLevelEnum.MEDIUM
    status: CapaStatusEnum = CapaStatusEnum.PENDING

class CapaCreate(CapaBase):
    audit_id: Optional[uuid.UUID] = None
    question_id: Optional[uuid.UUID] = None
    department_id: int
    assigned_to: uuid.UUID

class CapaUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    deadline: Optional[date] = None
    priority: Optional[RiskLevelEnum] = None
    status: Optional[CapaStatusEnum] = None
    root_cause_analysis: Optional[str] = Field(None, max_length=2000)
    corrective_action: Optional[str] = Field(None, max_length=2000)
    preventive_action: Optional[str] = Field(None, max_length=2000)
    assigned_to: Optional[uuid.UUID] = None

class CapaResponse(CapaBase):
    id: uuid.UUID
    audit_id: Optional[uuid.UUID]
    question_id: Optional[uuid.UUID]
    department_id: int
    department_name: str
    assigned_to: uuid.UUID
    assigned_name: str
    created_by: uuid.UUID
    created_name: str
    approved_by: Optional[uuid.UUID] = None
    approved_name: Optional[str] = None
    root_cause_analysis: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    evidence: List[CapaEvidenceResponse] = []

    class Config:
        from_attributes = True

class PaginatedCapas(BaseModel):
    items: List[CapaResponse]
    total: int
    page: int
    pages: int
    size: int

# Notification Schemas
class NotificationBase(BaseModel):
    title: str = Field(..., max_length=150)
    message: str = Field(..., max_length=1000)
    channel: NotifyChannelEnum = NotifyChannelEnum.IN_APP

class NotificationCreate(NotificationBase):
    user_id: uuid.UUID

class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
