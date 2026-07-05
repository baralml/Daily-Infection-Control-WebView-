import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.models.audit import ResponseTypeEnum, AuditStatusEnum, RiskLevelEnum, MediaTypeEnum

# Department Schemas
class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=10)

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Question Schemas
class QuestionBase(BaseModel):
    text: str = Field(..., max_length=500)
    response_type: ResponseTypeEnum
    options: Optional[List[str]] = None
    compliance_weight: int = Field(1, ge=0)
    is_required: bool = True
    is_active: bool = True
    order_num: int

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: uuid.UUID
    group_id: uuid.UUID

    class Config:
        from_attributes = True

# Question Group Schemas
class QuestionGroupBase(BaseModel):
    title: str = Field(..., max_length=150)
    order_num: int

class QuestionGroupCreate(QuestionGroupBase):
    pass

class QuestionGroupResponse(QuestionGroupBase):
    id: uuid.UUID
    template_id: uuid.UUID
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True

# Audit Template Schemas
class AuditTemplateBase(BaseModel):
    title: str = Field(..., max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True

class AuditTemplateCreate(AuditTemplateBase):
    pass

class AuditTemplateResponse(AuditTemplateBase):
    id: uuid.UUID
    version: int
    created_by: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AuditTemplateDetailResponse(AuditTemplateResponse):
    question_groups: List[QuestionGroupResponse] = []

    class Config:
        from_attributes = True

# Audit Response Media Schemas
class AuditResponseMediaBase(BaseModel):
    media_type: MediaTypeEnum
    original_url: str
    thumbnail_url: Optional[str] = None
    compressed_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    media_metadata: Optional[Dict[str, Any]] = None

class AuditResponseMediaCreate(AuditResponseMediaBase):
    pass

class AuditResponseMediaResponse(AuditResponseMediaBase):
    id: uuid.UUID
    response_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Audit Response Schemas
class AuditResponseBase(BaseModel):
    answer: str = Field(..., max_length=2000)
    remarks: Optional[str] = Field(None, max_length=1000)

class AuditResponseCreate(AuditResponseBase):
    question_id: uuid.UUID

class AuditResponseResponse(AuditResponseBase):
    id: uuid.UUID
    audit_id: uuid.UUID
    question_id: uuid.UUID
    score: float
    created_at: datetime
    media: List[AuditResponseMediaResponse] = []

    class Config:
        from_attributes = True

# Audit Schemas
class AuditBase(BaseModel):
    template_id: uuid.UUID
    department_id: int
    audited_at: datetime
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    device_id: Optional[str] = None

class AuditCreate(AuditBase):
    pass

class AuditResponseUpdateBatch(BaseModel):
    responses: List[AuditResponseCreate]

class AuditResponseDetail(BaseModel):
    response_id: uuid.UUID
    question_id: uuid.UUID
    text: str
    response_type: ResponseTypeEnum
    options: Optional[List[str]] = None
    compliance_weight: int
    group_title: str
    answer: Optional[str] = None
    score: float = 0.0
    remarks: Optional[str] = None
    media: List[AuditResponseMediaResponse] = []

class AuditResponseGroupDetail(BaseModel):
    group_id: uuid.UUID
    title: str
    order_num: int
    score: float = 0.0
    questions: List[AuditResponseDetail] = []

class AuditDetailResponse(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    template_title: str
    department_id: int
    department_name: str
    auditor_id: uuid.UUID
    auditor_name: str
    status: AuditStatusEnum
    compliance_percentage: float
    overall_score: float
    risk_level: RiskLevelEnum
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    device_id: Optional[str] = None
    audited_at: datetime
    created_at: datetime
    updated_at: datetime
    groups: List[AuditResponseGroupDetail] = []

    class Config:
        from_attributes = True

class AuditSummaryResponse(BaseModel):
    id: uuid.UUID
    template_title: str
    department_name: str
    auditor_name: str
    status: AuditStatusEnum
    compliance_percentage: float
    overall_score: float
    risk_level: RiskLevelEnum
    audited_at: datetime

    class Config:
        from_attributes = True

class PaginatedAudits(BaseModel):
    items: List[AuditSummaryResponse]
    total: int
    page: int
    pages: int
    size: int
