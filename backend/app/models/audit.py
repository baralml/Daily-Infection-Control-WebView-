from datetime import datetime, timezone
import uuid
import enum
from typing import List, Optional
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class ResponseTypeEnum(str, enum.Enum):
    RADIO = "RADIO"
    CHECKBOX = "CHECKBOX"
    DROPDOWN = "DROPDOWN"
    TEXT = "TEXT"
    LONG_TEXT = "LONG_TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    IMAGE_UPLOAD = "IMAGE_UPLOAD"
    SIGNATURE = "SIGNATURE"
    BARCODE = "BARCODE"
    QR_SCAN = "QR_SCAN"

class AuditStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"

class RiskLevelEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class MediaTypeEnum(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    audits: Mapped[List["Audit"]] = relationship("Audit", back_populates="department")
    capas: Mapped[List["Capa"]] = relationship("Capa", back_populates="department")

class AuditTemplate(Base):
    __tablename__ = "audit_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    question_groups: Mapped[List["QuestionGroup"]] = relationship("QuestionGroup", back_populates="template", cascade="all, delete-orphan", order_by="QuestionGroup.order_num")
    audits: Mapped[List["Audit"]] = relationship("Audit", back_populates="template")

class QuestionGroup(Base):
    __tablename__ = "question_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_templates.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    template: Mapped["AuditTemplate"] = relationship("AuditTemplate", back_populates="question_groups")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="group", cascade="all, delete-orphan", order_by="Question.order_num")

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("question_groups.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    response_type: Mapped[ResponseTypeEnum] = mapped_column(Enum(ResponseTypeEnum), nullable=False, default=ResponseTypeEnum.RADIO)
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # list of choices e.g. ["Yes", "No", "N/A"]
    compliance_weight: Mapped[int] = mapped_column(Integer, default=1)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    group: Mapped["QuestionGroup"] = relationship("QuestionGroup", back_populates="questions")
    responses: Mapped[List["AuditResponse"]] = relationship("AuditResponse", back_populates="question")

class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_templates.id", ondelete="RESTRICT"), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    auditor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[AuditStatusEnum] = mapped_column(Enum(AuditStatusEnum), nullable=False, default=AuditStatusEnum.DRAFT)
    compliance_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00)
    overall_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00)
    risk_level: Mapped[RiskLevelEnum] = mapped_column(Enum(RiskLevelEnum), nullable=False, default=RiskLevelEnum.LOW)
    gps_latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    gps_longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    template: Mapped["AuditTemplate"] = relationship("AuditTemplate", back_populates="audits")
    department: Mapped["Department"] = relationship("Department", back_populates="audits")
    auditor: Mapped["User"] = relationship("User", back_populates="audits")
    responses: Mapped[List["AuditResponse"]] = relationship("AuditResponse", back_populates="audit", cascade="all, delete-orphan")
    capas: Mapped[List["Capa"]] = relationship("Capa", back_populates="audit")

    @property
    def template_title(self) -> str:
        return self.template.title if self.template else ""

    @property
    def department_name(self) -> str:
        return self.department.name if self.department else ""

    @property
    def auditor_name(self) -> str:
        return self.auditor.full_name if self.auditor else ""

class AuditResponse(Base):
    __tablename__ = "audit_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    answer: Mapped[str] = mapped_column(String(2000), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00)
    remarks: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    audit: Mapped["Audit"] = relationship("Audit", back_populates="responses")
    question: Mapped["Question"] = relationship("Question", back_populates="responses")
    media: Mapped[List["AuditResponseMedia"]] = relationship("AuditResponseMedia", back_populates="response", cascade="all, delete-orphan")

class AuditResponseMedia(Base):
    __tablename__ = "audit_response_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_responses.id", ondelete="CASCADE"), nullable=False)
    media_type: Mapped[MediaTypeEnum] = mapped_column(Enum(MediaTypeEnum), nullable=False, default=MediaTypeEnum.IMAGE)
    original_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    compressed_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    media_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    response: Mapped["AuditResponse"] = relationship("AuditResponse", back_populates="media")
