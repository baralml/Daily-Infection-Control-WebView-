import uuid
import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum, JSON, Numeric, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.audit import RiskLevelEnum

class RoundStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"

class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    floors: Mapped[List["BuildingFloor"]] = relationship("BuildingFloor", back_populates="building", cascade="all, delete-orphan")

class BuildingFloor(Base):
    __tablename__ = "building_floors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    floor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    building: Mapped["Building"] = relationship("Building", back_populates="floors")
    departments: Mapped[List["BuildingDepartment"]] = relationship("BuildingDepartment", back_populates="floor", cascade="all, delete-orphan")

class BuildingDepartment(Base):
    __tablename__ = "building_departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("building_floors.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    floor: Mapped["BuildingFloor"] = relationship("BuildingFloor", back_populates="departments")
    department = relationship("Department")
    rooms: Mapped[List["BuildingRoom"]] = relationship("BuildingRoom", back_populates="building_department", order_by="BuildingRoom.room_number", cascade="all, delete-orphan")

class BuildingRoom(Base):
    __tablename__ = "building_rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("building_departments.id", ondelete="CASCADE"), nullable=False)
    room_number: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    building_department: Mapped["BuildingDepartment"] = relationship("BuildingDepartment", back_populates="rooms")

class DailyRound(Base):
    __tablename__ = "daily_rounds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital: Mapped[str] = mapped_column(String(100), nullable=False)
    building: Mapped[str] = mapped_column(String(100), nullable=False)
    building_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True)
    floor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Nullable: selected during walkthrough
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=True)  # Nullable: selected during walkthrough
    round_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Morning, Afternoon, Evening, Night
    auditor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[RoundStatusEnum] = mapped_column(Enum(RoundStatusEnum), nullable=False, default=RoundStatusEnum.DRAFT)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    department = relationship("Department")
    auditor = relationship("User")
    building_obj: Mapped[Optional["Building"]] = relationship("Building")
    observations: Mapped[List["DailyRoundObservation"]] = relationship("DailyRoundObservation", back_populates="round", cascade="all, delete-orphan")
    floor_states: Mapped[List["DailyRoundFloorState"]] = relationship("DailyRoundFloorState", back_populates="round", cascade="all, delete-orphan")

class DailyRoundFloorState(Base):
    __tablename__ = "daily_round_floor_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_rounds.id", ondelete="CASCADE"), nullable=False)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("building_floors.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="BLUE")  # BLUE, ORANGE, GREEN, RED
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    round: Mapped["DailyRound"] = relationship("DailyRound", back_populates="floor_states")
    floor: Mapped["BuildingFloor"] = relationship("BuildingFloor")

class DailyRoundObservation(Base):
    __tablename__ = "daily_round_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_rounds.id", ondelete="CASCADE"), nullable=False)
    floor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    floor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("building_floors.id", ondelete="SET NULL"), nullable=True)
    building_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("building_departments.id", ondelete="SET NULL"), nullable=True)
    
    observation_text: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    room_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    severity: Mapped[RiskLevelEnum] = mapped_column(Enum(RiskLevelEnum), nullable=False, default=RiskLevelEnum.MEDIUM)
    remarks: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    voice_note_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    voice_text_transcript: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    has_capa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    round: Mapped["DailyRound"] = relationship("DailyRound", back_populates="observations")
    department = relationship("Department")
    floor: Mapped[Optional["BuildingFloor"]] = relationship("BuildingFloor")
    building_department: Mapped[Optional["BuildingDepartment"]] = relationship("BuildingDepartment")
    media: Mapped[List["DailyRoundObservationMedia"]] = relationship("DailyRoundObservationMedia", back_populates="observation", cascade="all, delete-orphan")
    capas: Mapped[List["Capa"]] = relationship("Capa", back_populates="daily_round_observation", cascade="all, delete-orphan")

class DailyRoundObservationMedia(Base):
    __tablename__ = "daily_round_observation_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    observation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_round_observations.id", ondelete="CASCADE"), nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), default="IMAGE") # IMAGE, VIDEO, AUDIO
    original_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    compressed_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    observation: Mapped["DailyRoundObservation"] = relationship("DailyRoundObservation", back_populates="media")

class MasterObservation(Base):
    __tablename__ = "master_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    default_severity: Mapped[RiskLevelEnum] = mapped_column(Enum(RiskLevelEnum), nullable=False, default=RiskLevelEnum.MEDIUM)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class StaffReport(Base):
    __tablename__ = "staff_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
