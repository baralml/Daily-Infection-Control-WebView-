from datetime import datetime, date, timezone
import uuid
import enum
from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.audit import RiskLevelEnum

class CapaStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class NotifyChannelEnum(str, enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    SMS = "SMS"

class Capa(Base):
    __tablename__ = "capas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("audits.id", ondelete="SET NULL"), nullable=True)
    question_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    daily_round_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("daily_round_observations.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    assigned_to: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[RiskLevelEnum] = mapped_column(Enum(RiskLevelEnum), nullable=False, default=RiskLevelEnum.MEDIUM)
    status: Mapped[CapaStatusEnum] = mapped_column(Enum(CapaStatusEnum), nullable=False, default=CapaStatusEnum.PENDING)
    root_cause_analysis: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    corrective_action: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    preventive_action: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    audit: Mapped[Optional["Audit"]] = relationship("Audit", back_populates="capas")
    daily_round_observation: Mapped[Optional["DailyRoundObservation"]] = relationship("DailyRoundObservation", back_populates="capas")
    department: Mapped["Department"] = relationship("Department", back_populates="capas")
    evidence: Mapped[List["CapaEvidence"]] = relationship("CapaEvidence", back_populates="capa", cascade="all, delete-orphan")

class CapaEvidence(Base):
    __tablename__ = "capa_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    capa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("capas.id", ondelete="CASCADE"), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    capa: Mapped["Capa"] = relationship("Capa", back_populates="evidence")

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    channel: Mapped[NotifyChannelEnum] = mapped_column(Enum(NotifyChannelEnum), nullable=False, default=NotifyChannelEnum.IN_APP)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
