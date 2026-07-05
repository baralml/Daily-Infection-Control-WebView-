import uuid
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, PermissionChecker
from app.models.auth import User, Role
from app.schemas.staff_report import StaffReportResponse, StaffReportCreate
from app.crud.crud_staff_report import create_staff_report, get_staff_reports, get_staff_report_by_id, update_staff_report_resolve
from app.services.storage import upload_file_to_s3
from app.services.notification import dispatch_notification_to_user

router = APIRouter()

@router.post("", response_model=StaffReportResponse, status_code=status.HTTP_201_CREATED)
async def post_staff_report(
    description: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
) -> Any:
    """Public endpoint for staff to report infection control non-conformances with photo evidence and GPS coordinates."""
    photo_url = None
    if file:
        contents = await file.read()
        unique_prefix = uuid.uuid4().hex
        file_key = f"staff_reports/{unique_prefix}_{file.filename}"
        photo_url = upload_file_to_s3(contents, file_key, file.content_type)
        
    obj_in = StaffReportCreate(
        description=description,
        latitude=latitude,
        longitude=longitude
    )
    db_report = create_staff_report(db, obj_in, photo_url)
    
    # Notify all admin users about the new safety report
    try:
        admins = db.query(User).join(Role).filter(Role.name.in_(["SUPER ADMIN", "HOSPITAL ADMIN"])).all()
        for admin in admins:
            dispatch_notification_to_user(
                db,
                admin.id,
                title="🚨 New Staff Safety Report Submitted",
                message=f"Anonymous report logged: '{description[:80]}...'"
            )
    except Exception as e:
        print(f"Failed to dispatch notifications: {e}", flush=True)
        
    return db_report

@router.get("", response_model=List[StaffReportResponse])
def list_staff_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("users", "read"))
) -> Any:
    """Admin-only endpoint to retrieve all anonymous staff reports."""
    return get_staff_reports(db, skip=skip, limit=limit)

@router.patch("/{report_id}/resolve", response_model=StaffReportResponse)
def resolve_staff_report(
    report_id: uuid.UUID,
    is_resolved: bool = True,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("users", "write"))
) -> Any:
    """Admin-only endpoint to mark a staff report as resolved/reviewed."""
    db_report = get_staff_report_by_id(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Staff report not found")
    return update_staff_report_resolve(db, db_report, is_resolved)
