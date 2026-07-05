import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.daily_round import StaffReport
from app.schemas.staff_report import StaffReportCreate

def create_staff_report(db: Session, obj_in: StaffReportCreate, photo_url: Optional[str] = None) -> StaffReport:
    db_report = StaffReport(
        id=uuid.uuid4(),
        description=obj_in.description,
        latitude=obj_in.latitude,
        longitude=obj_in.longitude,
        photo_url=photo_url,
        is_resolved=False
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_staff_report_by_id(db: Session, report_id: uuid.UUID) -> Optional[StaffReport]:
    return db.query(StaffReport).filter(StaffReport.id == report_id).first()

def get_staff_reports(db: Session, skip: int = 0, limit: int = 100) -> List[StaffReport]:
    return db.query(StaffReport).order_by(desc(StaffReport.created_at)).offset(skip).limit(limit).all()

def update_staff_report_resolve(db: Session, db_report: StaffReport, is_resolved: bool) -> StaffReport:
    db_report.is_resolved = is_resolved
    db.commit()
    db.refresh(db_report)
    return db_report
