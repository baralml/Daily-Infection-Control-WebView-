import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, PermissionChecker
from app.models.auth import User
from app.models.audit import AuditTemplate, QuestionGroup, Question
from app.schemas.audit import (
    AuditTemplateResponse, AuditTemplateDetailResponse, AuditTemplateCreate,
    QuestionGroupResponse, QuestionGroupCreate, QuestionResponse, QuestionCreate
)
from app.crud.crud_audit import get_active_templates, get_template_details

router = APIRouter()

@router.get("", response_model=List[AuditTemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> List[AuditTemplate]:
    """Lists all active audit templates."""
    return get_active_templates(db)

@router.get("/{template_id}", response_model=AuditTemplateDetailResponse)
def get_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieves full nested structure of a single audit template."""
    template = get_template_details(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Audit template not found")
    return template

@router.post("", response_model=AuditTemplateDetailResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    obj_in: AuditTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("checklists", "write"))
) -> Any:
    """Admin endpoint to create a blank master audit checklist template."""
    db_template = AuditTemplate(
        title=obj_in.title,
        description=obj_in.description,
        is_active=obj_in.is_active,
        created_by=current_user.id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.post("/{template_id}/groups", response_model=QuestionGroupResponse, status_code=status.HTTP_201_CREATED)
def create_template_group(
    template_id: uuid.UUID,
    obj_in: QuestionGroupCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("checklists", "write"))
) -> Any:
    """Admin endpoint to create a question group inside a template."""
    # Verify template exists
    template = db.query(AuditTemplate).filter(AuditTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Audit template not found")
        
    db_group = QuestionGroup(
        template_id=template_id,
        title=obj_in.title,
        order_num=obj_in.order_num
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.post("/groups/{group_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_group_question(
    group_id: uuid.UUID,
    obj_in: QuestionCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("checklists", "write"))
) -> Any:
    """Admin endpoint to create a question inside a section group."""
    # Verify group exists
    group = db.query(QuestionGroup).filter(QuestionGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Question group not found")
        
    db_question = Question(
        group_id=group_id,
        text=obj_in.text,
        response_type=obj_in.response_type,
        options=obj_in.options,
        compliance_weight=obj_in.compliance_weight,
        is_required=obj_in.is_required,
        is_active=obj_in.is_active,
        order_num=obj_in.order_num
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question
