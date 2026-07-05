import uuid
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Response
from app.services.reporting import generate_pdf_capa_report
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, PermissionChecker
from app.models.auth import User
from app.models.capa import CapaStatusEnum, Capa
from app.schemas.capa import PaginatedCapas, CapaResponse, CapaUpdate, CapaEvidenceResponse
from app.crud.crud_capa import get_capas_paginated, get_capa_by_id, update_capa, add_capa_evidence, get_capa_detailed
from app.models.audit import RiskLevelEnum
from app.services.storage import upload_file_to_s3
from app.services.notification import dispatch_notification_to_user
from app.models.capa import NotifyChannelEnum

router = APIRouter()

@router.get("", response_model=PaginatedCapas)
def list_capas(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    department_id: Optional[int] = Query(None),
    status: Optional[CapaStatusEnum] = Query(None),
    priority: Optional[RiskLevelEnum] = Query(None),
    assigned_to: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("capa", "read"))
) -> Any:
    """Lists corrective actions (CAPA) based on filters, with pagination."""
    items, total = get_capas_paginated(
        db, page=page, size=size, department_id=department_id,
        status=status, priority=priority, assigned_to=assigned_to
    )
    
    pages = (total + size - 1) // size
    
    formatted_items = []
    for item in items:
        # Load user names for schema
        from app.crud.crud_user import get_user
        assigned = get_user(db, item.assigned_to)
        creator = get_user(db, item.created_by)
        approver = get_user(db, item.approved_by) if item.approved_by else None
        
        formatted_items.append({
            "id": item.id,
            "audit_id": item.audit_id,
            "question_id": item.question_id,
            "department_id": item.department_id,
            "department_name": item.department.name,
            "assigned_to": item.assigned_to,
            "assigned_name": assigned.full_name if assigned else "Unknown",
            "created_by": item.created_by,
            "created_name": creator.full_name if creator else "System",
            "approved_by": item.approved_by,
            "approved_name": approver.full_name if approver else None,
            "title": item.title,
            "description": item.description,
            "deadline": item.deadline,
            "priority": item.priority,
            "status": item.status,
            "root_cause_analysis": item.root_cause_analysis,
            "corrective_action": item.corrective_action,
            "preventive_action": item.preventive_action,
            "closed_at": item.closed_at,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "evidence": []
        })
        
    return {
        "items": formatted_items,
        "total": total,
        "page": page,
        "pages": pages,
        "size": size
    }

@router.get("/{capa_id}/pdf")
def download_capa_pdf(
    capa_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("capa", "read"))
):
    """Generates and downloads a printable PDF report for the CAPA action plan."""
    capa = get_capa_detailed(db, capa_id)
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
        
    from app.crud.crud_user import get_user
    assigned = get_user(db, capa.assigned_to)
    creator = get_user(db, capa.created_by)
    
    pdf_bytes = generate_pdf_capa_report(
        capa,
        assignee_name=assigned.full_name if assigned else "Unknown",
        creator_name=creator.full_name if creator else "System"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CAPA_Plan_{capa_id}.pdf"}
    )

@router.get("/{capa_id}", response_model=CapaResponse)
def get_capa_details(
    capa_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("capa", "read"))
) -> Any:
    """Retrieves full details for a single CAPA ticket, including proof of closure."""
    item = get_capa_detailed(db, capa_id)
    if not item:
        raise HTTPException(status_code=404, detail="CAPA not found")
        
    from app.crud.crud_user import get_user
    assigned = get_user(db, item.assigned_to)
    creator = get_user(db, item.created_by)
    approver = get_user(db, item.approved_by) if item.approved_by else None
    
    evidence_resp = []
    for ev in item.evidence:
        evidence_resp.append({
            "id": ev.id,
            "capa_id": ev.capa_id,
            "uploaded_by": ev.uploaded_by,
            "file_url": ev.file_url,
            "mime_type": ev.mime_type,
            "created_at": ev.created_at
        })
        
    return {
        "id": item.id,
        "audit_id": item.audit_id,
        "question_id": item.question_id,
        "department_id": item.department_id,
        "department_name": item.department.name,
        "assigned_to": item.assigned_to,
        "assigned_name": assigned.full_name if assigned else "Unknown",
        "created_by": item.created_by,
        "created_name": creator.full_name if creator else "System",
        "approved_by": item.approved_by,
        "approved_name": approver.full_name if approver else None,
        "title": item.title,
        "description": item.description,
        "deadline": item.deadline,
        "priority": item.priority,
        "status": item.status,
        "root_cause_analysis": item.root_cause_analysis,
        "corrective_action": item.corrective_action,
        "preventive_action": item.preventive_action,
        "closed_at": item.closed_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "evidence": evidence_resp
    }

@router.put("/{capa_id}", response_model=CapaResponse)
def modify_capa(
    capa_id: uuid.UUID,
    obj_in: CapaUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("capa", "write"))
) -> Any:
    """Updates CAPA ticket description, RCA details, and corrective/preventive plans."""
    item = get_capa_by_id(db, capa_id)
    if not item:
        raise HTTPException(status_code=404, detail="CAPA not found")
        
    update_capa(db, item, obj_in)
    return get_capa_details(capa_id, db)

@router.post("/{capa_id}/evidence", response_model=CapaEvidenceResponse)
async def upload_capa_evidence(
    capa_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("capa", "write"))
) -> Any:
    """Adds resolution proof files (images/PDFs) to a pending CAPA ticket."""
    item = get_capa_by_id(db, capa_id)
    if not item:
        raise HTTPException(status_code=404, detail="CAPA not found")
        
    contents = await file.read()
    unique_prefix = uuid.uuid4().hex
    file_key = f"capa_evidence/{unique_prefix}_{file.filename}"
    
    file_url = upload_file_to_s3(contents, file_key, file.content_type)
    evidence = add_capa_evidence(db, capa_id, current_user.id, file_url, file.content_type)
    
    # Notify creator of upload (ICO or Quality Manager)
    dispatch_notification_to_user(
        db, item.created_by, "CAPA EVIDENCE UPLOADED",
        f"User '{current_user.full_name}' uploaded evidence for CAPA '{item.title}'",
        [NotifyChannelEnum.IN_APP]
    )
    
    return evidence

@router.post("/{capa_id}/approve", response_model=CapaResponse)
def approve_capa_resolution(
    capa_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("capa", "approve"))
) -> Any:
    """Closes CAPA ticket. Limited to Quality Manager or Infection Control Officer roles."""
    item = get_capa_by_id(db, capa_id)
    if not item:
        raise HTTPException(status_code=404, detail="CAPA not found")
        
    item.status = CapaStatusEnum.CLOSED
    item.approved_by = current_user.id
    item.closed_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()
    db.commit()
    
    # Notify assigned user of closure
    dispatch_notification_to_user(
        db, item.assigned_to, "CAPA CLOSED AND APPROVED",
        f"Corrective action CAPA '{item.title}' has been successfully approved and closed.",
        [NotifyChannelEnum.IN_APP, NotifyChannelEnum.EMAIL]
    )
    
    return get_capa_details(capa_id, db)
