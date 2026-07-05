import uuid
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.capa import Capa, CapaEvidence, Notification, CapaStatusEnum, NotifyChannelEnum
from app.models.audit import RiskLevelEnum
from app.schemas.capa import CapaCreate, CapaUpdate, NotificationCreate

def create_capa(db: Session, obj_in: CapaCreate, creator_id: uuid.UUID) -> Capa:
    db_capa = Capa(
        audit_id=obj_in.audit_id,
        question_id=obj_in.question_id,
        department_id=obj_in.department_id,
        assigned_to=obj_in.assigned_to,
        created_by=creator_id,
        title=obj_in.title,
        description=obj_in.description,
        deadline=obj_in.deadline,
        priority=obj_in.priority,
        status=obj_in.status
    )
    db.add(db_capa)
    db.commit()
    db.refresh(db_capa)
    return db_capa

def get_capa_by_id(db: Session, capa_id: uuid.UUID) -> Optional[Capa]:
    return db.query(Capa).filter(Capa.id == capa_id).first()

def get_capa_detailed(db: Session, capa_id: uuid.UUID) -> Optional[Capa]:
    return db.query(Capa).options(
        joinedload(Capa.evidence)
    ).filter(Capa.id == capa_id).first()

def get_capas_paginated(
    db: Session,
    page: int = 1,
    size: int = 10,
    department_id: Optional[int] = None,
    status: Optional[CapaStatusEnum] = None,
    priority: Optional[RiskLevelEnum] = None,
    assigned_to: Optional[uuid.UUID] = None
) -> Tuple[List[Capa], int]:
    query = db.query(Capa)
    if department_id is not None:
        query = query.filter(Capa.department_id == department_id)
    if status is not None:
        query = query.filter(Capa.status == status)
    if priority is not None:
        query = query.filter(Capa.priority == priority)
    if assigned_to is not None:
        query = query.filter(Capa.assigned_to == assigned_to)
        
    total = query.count()
    items = query.order_by(desc(Capa.created_at)).offset((page - 1) * size).limit(size).all()
    return items, total

def update_capa(db: Session, db_capa: Capa, obj_in: CapaUpdate) -> Capa:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_capa, field, value)
        
    if obj_in.status == CapaStatusEnum.CLOSED:
        db_capa.closed_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_capa)
    return db_capa

def add_capa_evidence(db: Session, capa_id: uuid.UUID, uploaded_by: uuid.UUID, file_url: str, mime_type: Optional[str] = None) -> CapaEvidence:
    evidence = CapaEvidence(
        capa_id=capa_id,
        uploaded_by=uploaded_by,
        file_url=file_url,
        mime_type=mime_type
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence

# Notification helper functions
def create_notification(db: Session, obj_in: NotificationCreate) -> Notification:
    db_notify = Notification(
        user_id=obj_in.user_id,
        title=obj_in.title,
        message=obj_in.message,
        channel=obj_in.channel
    )
    db.add(db_notify)
    db.commit()
    db.refresh(db_notify)
    return db_notify

def get_user_notifications(db: Session, user_id: uuid.UUID, limit: int = 50) -> List[Notification]:
    return db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(desc(Notification.created_at)).limit(limit).all()

def mark_notification_as_read(db: Session, notification_id: uuid.UUID) -> Optional[Notification]:
    db_notify = db.query(Notification).filter(Notification.id == notification_id).first()
    if db_notify:
        db_notify.is_read = True
        db_notify.read_at = datetime.utcnow()
        db.commit()
        db.refresh(db_notify)
    return db_notify
