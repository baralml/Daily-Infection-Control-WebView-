import uuid
from datetime import datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, PermissionChecker
from app.models.auth import User
from app.models.audit import AuditStatusEnum, RiskLevelEnum, MediaTypeEnum, AuditResponse
from app.schemas.audit import (
    PaginatedAudits, AuditCreate, AuditDetailResponse, AuditResponseUpdateBatch,
    AuditResponseMediaResponse, DepartmentResponse, DepartmentCreate
)
from app.crud.crud_audit import (
    get_audits_paginated, create_audit, get_audit_detailed_responses,
    update_audit_responses, add_response_media, get_departments, create_department,
    get_department_by_code
)
from app.services.scoring import calculate_audit_scores, auto_generate_capas
from app.services.storage import process_and_store_media
from app.services.reporting import generate_pdf_audit_report, generate_excel_report
from app.services.notification import dispatch_notification_to_user
from app.models.capa import NotifyChannelEnum

router = APIRouter()

@router.get("", response_model=PaginatedAudits)
def list_audits(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    department_id: Optional[int] = Query(None),
    status: Optional[AuditStatusEnum] = Query(None),
    risk_level: Optional[RiskLevelEnum] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("audits", "read"))
) -> Any:
    """Lists audits based on filters, with pagination."""
    items, total = get_audits_paginated(
        db, page=page, size=size, department_id=department_id,
        status=status, risk_level=risk_level, start_date=start_date, end_date=end_date
    )
    
    pages = (total + size - 1) // size
    
    summary_items = []
    for audit in items:
        summary_items.append({
            "id": audit.id,
            "template_title": audit.template.title,
            "department_name": audit.department.name,
            "auditor_name": audit.auditor.full_name,
            "status": audit.status,
            "compliance_percentage": float(audit.compliance_percentage),
            "overall_score": float(audit.overall_score),
            "risk_level": audit.risk_level,
            "audited_at": audit.audited_at
        })
        
    return {
        "items": summary_items,
        "total": total,
        "page": page,
        "pages": pages,
        "size": size
    }

@router.post("", response_model=AuditDetailResponse, status_code=status.HTTP_201_CREATED)
def init_audit_sheet(
    obj_in: AuditCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("audits", "write"))
) -> Any:
    """Initializes a new audit instance in Draft mode."""
    new_audit = create_audit(db, obj_in, current_user.id)
    # Pre-populate empty response entries for all template questions
    from app.models.audit import AuditTemplate, Question
    template = db.query(AuditTemplate).filter(AuditTemplate.id == new_audit.template_id).first()
    if template:
        for group in template.question_groups:
            for question in group.questions:
                # Add default unanswered audit response
                default_resp = AuditResponse(
                    audit_id=new_audit.id,
                    question_id=question.id,
                    answer="N/A",  # Default to Not Applicable
                    score=0.0,
                    remarks=""
                )
                db.add(default_resp)
        db.commit()
        
    return get_audit_details(new_audit.id, db, current_user)

@router.get("/{audit_id}", response_model=AuditDetailResponse)
def get_audit_details(
    audit_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("audits", "read"))
) -> Any:
    """Retrieves full nested structured response state for an audit."""
    audit = get_audit_detailed_responses(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    # Group responses by question groups for schema rendering
    group_map = {}
    for resp in audit.responses:
        q = resp.question
        g = q.group
        
        if g.id not in group_map:
            group_map[g.id] = {
                "group_id": g.id,
                "title": g.title,
                "order_num": g.order_num,
                "questions": []
            }
            
        group_map[g.id]["questions"].append({
            "response_id": resp.id,
            "question_id": q.id,
            "text": q.text,
            "response_type": q.response_type,
            "options": q.options,
            "compliance_weight": q.compliance_weight,
            "group_title": g.title,
            "answer": resp.answer,
            "score": float(resp.score),
            "remarks": resp.remarks,
            "media": resp.media
        })
        
    sorted_groups = sorted(list(group_map.values()), key=lambda x: x["order_num"])
    
    # Calculate group score percentages
    for g in sorted_groups:
        total_score = sum(q["score"] for q in g["questions"])
        total_weight = sum(q["compliance_weight"] for q in g["questions"] if q["answer"].upper() not in ["N/A", "NA"])
        g["score"] = round((total_score / total_weight) * 100.0, 2) if total_weight > 0 else 0.00
        # Sort questions within group
        # Sort using database order or mapping
        
    return {
        "id": audit.id,
        "template_id": audit.template_id,
        "template_title": audit.template.title,
        "department_id": audit.department_id,
        "department_name": audit.department.name,
        "auditor_id": audit.auditor_id,
        "auditor_name": audit.auditor.full_name,
        "status": audit.status,
        "compliance_percentage": float(audit.compliance_percentage),
        "overall_score": float(audit.overall_score),
        "risk_level": audit.risk_level,
        "gps_latitude": audit.gps_latitude,
        "gps_longitude": audit.gps_longitude,
        "device_id": audit.device_id,
        "audited_at": audit.audited_at,
        "created_at": audit.created_at,
        "updated_at": audit.updated_at,
        "groups": sorted_groups
    }

@router.put("/{audit_id}/responses", response_model=AuditDetailResponse)
def update_responses(
    audit_id: uuid.UUID,
    payload: AuditResponseUpdateBatch,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("audits", "write"))
) -> Any:
    """Updates batch answers for an audit (Drafts only). Recalculates rolling scores."""
    audit = get_audit_detailed_responses(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != AuditStatusEnum.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot edit a submitted audit")
        
    update_audit_responses(db, audit_id, payload.responses)
    # Calculate scores on the fly
    calculate_audit_scores(db, audit_id)
    
    return get_audit_detailed_responses(db, audit_id)

@router.post("/{audit_id}/media", response_model=AuditResponseMediaResponse)
async def upload_audit_media(
    audit_id: uuid.UUID,
    response_id: uuid.UUID = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("audits", "write"))
) -> Any:
    """Uploads file evidence (photo/video) for a specific question response."""
    audit = get_audit_detailed_responses(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != AuditStatusEnum.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot upload to a submitted audit")
        
    # Verify response belongs to audit
    response = db.query(AuditResponse).filter(
        AuditResponse.id == response_id,
        AuditResponse.audit_id == audit_id
    ).first()
    if not response:
        raise HTTPException(status_code=400, detail="Response ID not found for this audit")
        
    contents = await file.read()
    file_size = len(contents)
    
    # Process S3 storage (compression, thumbs, EXIF strip)
    original, compressed, thumbnail = process_and_store_media(contents, file.filename, file.content_type)
    
    media_type = MediaTypeEnum.IMAGE
    if file.content_type.startswith("video/"):
        media_type = MediaTypeEnum.VIDEO
    elif file.content_type.startswith("audio/"):
        media_type = MediaTypeEnum.AUDIO
        
    db_media = add_response_media(
        db, response_id=response_id, media_type=media_type,
        original_url=original, thumbnail_url=thumbnail, compressed_url=compressed,
        file_size=file_size, mime_type=file.content_type
    )
    
    return db_media

@router.post("/{audit_id}/submit", response_model=AuditDetailResponse)
def submit_audit(
    audit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("audits", "write"))
) -> Any:
    """Finalizes scores, locks editing, auto-assigns CAPAs, and notifies management."""
    audit = get_audit_detailed_responses(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != AuditStatusEnum.DRAFT:
        raise HTTPException(status_code=400, detail="Audit is already submitted")
        
    # Complete score compiling
    calculate_audit_scores(db, audit_id)
    
    # Lock Audit
    audit.status = AuditStatusEnum.SUBMITTED
    audit.updated_at = datetime.utcnow()
    db.commit()
    
    # Auto-generate CAPAs for failed points
    capas_created = auto_generate_capas(db, audit_id, current_user.id)
    
    # If CRITICAL, trigger alerts to CEO & CHO
    if audit.risk_level == RiskLevelEnum.CRITICAL:
        from app.models.auth import Role
        from app.crud.crud_user import get_users
        users = db.query(User).join(Role).filter(Role.name.in_(["CEO", "CHO", "Quality Manager"])).all()
        alert_msg = (
            f"ALERT: Critical infection risk detected in department '{audit.department.name}' "
            f"during audit '{audit.template.title}' on {audit.audited_at.strftime('%Y-%m-%d')}. "
            f"Compliance Score: {audit.compliance_percentage}%."
        )
        for u in users:
            dispatch_notification_to_user(
                db, u.id, "CRITICAL RISK ALERT", alert_msg,
                [NotifyChannelEnum.IN_APP, NotifyChannelEnum.EMAIL]
            )
            
    return get_audit_detailed_responses(db, audit_id)

# Reporting endpoints
@router.get("/{audit_id}/pdf")
def export_audit_pdf(
    audit_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("reports", "read"))
):
    """Generates and serves a PDF summary document of the audit."""
    audit = get_audit_detailed_responses(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    pdf_bytes = generate_pdf_audit_report(audit)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Audit_{audit_id}.pdf"}
    )

@router.get("/export/excel")
def export_audits_excel(
    department_id: Optional[int] = Query(None),
    status: Optional[AuditStatusEnum] = Query(None),
    risk_level: Optional[RiskLevelEnum] = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("reports", "read"))
):
    """Compiles filtered audit lists into a structured Excel download."""
    audits, _ = get_audits_paginated(
        db, page=1, size=500, department_id=department_id,
        status=status, risk_level=risk_level
    )
    excel_bytes = generate_excel_report(audits)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Audits_Report.xlsx"}
    )

# Department Management
@router.get("/admin/departments", response_model=List[DepartmentResponse])
def get_all_departments(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> List[DepartmentResponse]:
    """Retrieve hospital departments listing."""
    return get_departments(db)

@router.post("/admin/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_new_department(
    obj_in: DepartmentCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("departments", "write"))
) -> DepartmentResponse:
    """Admin endpoint to create a hospital department."""
    existing = get_department_by_code(db, obj_in.code)
    if existing:
        raise HTTPException(status_code=400, detail="Department with this code already exists")
    return create_department(db, obj_in)
