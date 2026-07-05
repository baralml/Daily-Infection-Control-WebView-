import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, desc

from app.models.audit import (
    Department, AuditTemplate, QuestionGroup, Question,
    Audit, AuditResponse, AuditResponseMedia, ResponseTypeEnum,
    AuditStatusEnum, RiskLevelEnum, MediaTypeEnum
)
from app.schemas.audit import DepartmentCreate, AuditCreate, AuditResponseCreate

# Department CRUD
def get_department_by_code(db: Session, code: str) -> Optional[Department]:
    return db.query(Department).filter(Department.code == code).first()

def create_department(db: Session, obj_in: DepartmentCreate) -> Department:
    db_dept = Department(name=obj_in.name, code=obj_in.code)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

def get_departments(db: Session) -> List[Department]:
    return db.query(Department).order_by(Department.name).all()

def get_department(db: Session, dept_id: int) -> Optional[Department]:
    return db.query(Department).filter(Department.id == dept_id).first()

# Audit Template CRUD
def get_active_templates(db: Session) -> List[AuditTemplate]:
    return db.query(AuditTemplate).filter(AuditTemplate.is_active == True).order_by(AuditTemplate.title).all()

def get_template_details(db: Session, template_id: uuid.UUID) -> Optional[AuditTemplate]:
    """Fetch template with nested question groups and questions loaded."""
    return db.query(AuditTemplate).options(
        joinedload(AuditTemplate.question_groups).joinedload(QuestionGroup.questions)
    ).filter(AuditTemplate.id == template_id).first()

# Audit Creation & Fetching
def create_audit(db: Session, obj_in: AuditCreate, auditor_id: uuid.UUID) -> Audit:
    db_audit = Audit(
        template_id=obj_in.template_id,
        department_id=obj_in.department_id,
        auditor_id=auditor_id,
        status=AuditStatusEnum.DRAFT,
        gps_latitude=obj_in.gps_latitude,
        gps_longitude=obj_in.gps_longitude,
        device_id=obj_in.device_id,
        audited_at=obj_in.audited_at
    )
    db.add(db_audit)
    db.commit()
    db.refresh(db_audit)
    return db_audit

def get_audits_paginated(
    db: Session,
    page: int = 1,
    size: int = 10,
    department_id: Optional[int] = None,
    status: Optional[AuditStatusEnum] = None,
    risk_level: Optional[RiskLevelEnum] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Tuple[List[Audit], int]:
    """Retrieves paginated audits using joint filters."""
    query = db.query(Audit).options(
        joinedload(Audit.template),
        joinedload(Audit.department),
        joinedload(Audit.auditor)
    )
    if department_id is not None:
        query = query.filter(Audit.department_id == department_id)
    if status is not None:
        query = query.filter(Audit.status == status)
    if risk_level is not None:
        query = query.filter(Audit.risk_level == risk_level)
    if start_date is not None:
        query = query.filter(Audit.audited_at >= start_date)
    if end_date is not None:
        query = query.filter(Audit.audited_at <= end_date)
    
    total = query.count()
    items = query.order_by(desc(Audit.audited_at)).offset((page - 1) * size).limit(size).all()
    return items, total

def get_audit_by_id(db: Session, audit_id: uuid.UUID) -> Optional[Audit]:
    return db.query(Audit).filter(Audit.id == audit_id).first()

def get_audit_detailed_responses(db: Session, audit_id: uuid.UUID) -> Optional[Audit]:
    """Loads audit details plus related templates and response structures."""
    return db.query(Audit).options(
        joinedload(Audit.template),
        joinedload(Audit.department),
        joinedload(Audit.auditor),
        joinedload(Audit.responses).joinedload(AuditResponse.question).joinedload(Question.group),
        joinedload(Audit.responses).joinedload(AuditResponse.media)
    ).filter(Audit.id == audit_id).first()

# Responses and Media CRUD
def update_audit_responses(db: Session, audit_id: uuid.UUID, responses: List[AuditResponseCreate]) -> List[AuditResponse]:
    """Creates or updates responses for an audit.
    Recalculates individual scores (dependent on response).
    """
    updated_responses = []
    for resp in responses:
        # Check if response exists
        db_resp = db.query(AuditResponse).filter(
            AuditResponse.audit_id == audit_id,
            AuditResponse.question_id == resp.question_id
        ).first()
        
        # Load question weight to compute response score
        question = db.query(Question).filter(Question.id == resp.question_id).first()
        weight = question.compliance_weight if question else 1
        
        # Score mapping: Yes/YES = Weight, No/NO = 0, NA/Not Applicable = 0 (handled at group score sum filter)
        score = 0.0
        if resp.answer.upper() in ["YES", "Y", "TRUE"]:
            score = float(weight)
        elif resp.answer.upper() in ["NO", "N", "FALSE"]:
            score = 0.0
        
        if db_resp:
            db_resp.answer = resp.answer
            db_resp.remarks = resp.remarks
            db_resp.score = score
        else:
            db_resp = AuditResponse(
                audit_id=audit_id,
                question_id=resp.question_id,
                answer=resp.answer,
                remarks=resp.remarks,
                score=score
            )
            db.add(db_resp)
            
        updated_responses.append(db_resp)
        
    db.commit()
    return updated_responses

def add_response_media(
    db: Session,
    response_id: uuid.UUID,
    media_type: MediaTypeEnum,
    original_url: str,
    thumbnail_url: Optional[str] = None,
    compressed_url: Optional[str] = None,
    file_size: Optional[int] = None,
    mime_type: Optional[str] = None,
    media_metadata: Optional[dict] = None
) -> AuditResponseMedia:
    db_media = AuditResponseMedia(
        response_id=response_id,
        media_type=media_type,
        original_url=original_url,
        thumbnail_url=thumbnail_url,
        compressed_url=compressed_url,
        file_size=file_size,
        mime_type=mime_type,
        media_metadata=media_metadata
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media
