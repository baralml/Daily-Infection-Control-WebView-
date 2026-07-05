import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.audit import RiskLevelEnum
from app.models.daily_round import RoundStatusEnum
from app.schemas.audit import DepartmentResponse
from app.schemas.auth import UserResponse

class MasterObservationBase(BaseModel):
    text: str
    category: str
    default_severity: RiskLevelEnum
    is_active: bool = True

class MasterObservationResponse(MasterObservationBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class DailyRoundObservationMediaBase(BaseModel):
    media_type: str = "IMAGE"
    original_url: str
    thumbnail_url: Optional[str] = None
    compressed_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

class DailyRoundObservationMediaResponse(DailyRoundObservationMediaBase):
    id: uuid.UUID
    observation_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class CapaEmbeddedCreate(BaseModel):
    assigned_to: uuid.UUID
    deadline: str  # ISO date string (YYYY-MM-DD)
    priority: RiskLevelEnum = RiskLevelEnum.MEDIUM

class DailyRoundObservationCreate(BaseModel):
    observation_text: str = Field(..., max_length=500)
    category: str = Field(..., max_length=100)
    floor_name: str = Field(..., max_length=50)
    department_id: int
    room_number: Optional[str] = Field(None, max_length=50)
    severity: RiskLevelEnum = RiskLevelEnum.MEDIUM
    remarks: Optional[str] = Field(None, max_length=1000)
    voice_note_url: Optional[str] = Field(None, max_length=1000)
    voice_text_transcript: Optional[str] = Field(None, max_length=2000)
    has_capa: bool = False
    capa_details: Optional[CapaEmbeddedCreate] = None

class DailyRoundObservationResponse(BaseModel):
    id: uuid.UUID
    round_id: uuid.UUID
    floor_name: str
    department_id: int
    observation_text: str
    category: str
    room_number: Optional[str] = None
    severity: RiskLevelEnum
    remarks: Optional[str] = None
    voice_note_url: Optional[str] = None
    voice_text_transcript: Optional[str] = None
    has_capa: bool
    created_at: datetime
    updated_at: datetime
    media: List[DailyRoundObservationMediaResponse] = []
    department: Optional[DepartmentResponse] = None

    class Config:
        from_attributes = True

class DailyRoundCreate(BaseModel):
    hospital: str = Field(..., max_length=100)
    building: str = Field(..., max_length=100)
    building_id: Optional[uuid.UUID] = None
    floor: Optional[str] = Field(None, max_length=50)
    department_id: Optional[int] = None
    round_type: str = Field(..., max_length=50)  # Morning, Afternoon, Evening, Night

class DailyRoundFloorStateResponse(BaseModel):
    id: uuid.UUID
    round_id: uuid.UUID
    floor_id: uuid.UUID
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True

class DailyRoundResponse(BaseModel):
    id: uuid.UUID
    hospital: str
    building: str
    building_id: Optional[uuid.UUID] = None
    floor: Optional[str] = None
    department_id: Optional[int] = None
    round_type: str
    auditor_id: uuid.UUID
    status: str  # DRAFT or COMPLETED
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    department: Optional[DepartmentResponse] = None
    auditor: Optional[UserResponse] = None
    floor_states: List[DailyRoundFloorStateResponse] = []

    class Config:
        from_attributes = True

class DailyRoundDetailResponse(DailyRoundResponse):
    observations: List[DailyRoundObservationResponse] = []

    class Config:
        from_attributes = True

# ----------------- Layout Configuration Schemas -----------------
class BuildingCreate(BaseModel):
    name: str = Field(..., max_length=100)

class BuildingResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class BuildingRoomCreate(BaseModel):
    room_number: str = Field(..., max_length=50)

class BuildingRoomResponse(BaseModel):
    id: uuid.UUID
    building_department_id: uuid.UUID
    room_number: str

    class Config:
        from_attributes = True

class BuildingDepartmentCreate(BaseModel):
    department_id: int
    rooms: List[str] = []  # List of room numbers

class BuildingDepartmentResponse(BaseModel):
    id: uuid.UUID
    floor_id: uuid.UUID
    department_id: int
    department: Optional[DepartmentResponse] = None
    rooms: List[BuildingRoomResponse] = []

    class Config:
        from_attributes = True

class BuildingFloorCreate(BaseModel):
    floor_name: str = Field(..., max_length=50)
    order_index: int = 0
    departments: List[BuildingDepartmentCreate] = []

class BuildingFloorResponse(BaseModel):
    id: uuid.UUID
    building_id: uuid.UUID
    floor_name: str
    order_index: int
    departments: List[BuildingDepartmentResponse] = []

    class Config:
        from_attributes = True

class BuildingLayoutResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    floors: List[BuildingFloorResponse] = []

    class Config:
        from_attributes = True
