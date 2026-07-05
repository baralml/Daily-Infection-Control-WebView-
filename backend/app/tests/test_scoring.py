from datetime import datetime, timezone
import pytest
from app.models.auth import Role, User
from app.models.audit import (
    Department, AuditTemplate, QuestionGroup, Question,
    Audit, AuditResponse, ResponseTypeEnum, AuditStatusEnum, RiskLevelEnum
)
from app.services.scoring import calculate_audit_scores

def test_scoring_calculations(db):
    """Verifies compliance score averaging and risk level sorting."""
    # 1. Seed Roles, User and Department
    role = Role(name="ICO", permissions={})
    db.add(role)
    db.commit()
    
    user = User(email="ico@hosp.com", hashed_password="pw", full_name="Auditor", role_id=role.id)
    db.add(user)
    
    dept = Department(name="Intensive Care", code="ICU")
    db.add(dept)
    db.commit()
    
    # 2. Seed Audit template hierarchy
    template = AuditTemplate(title="Hand Wash Template", is_active=True)
    db.add(template)
    db.commit()
    
    group = QuestionGroup(template_id=template.id, title="Infrastructure", order_num=1)
    db.add(group)
    db.commit()
    
    q1 = Question(group_id=group.id, text="Sink clean?", response_type=ResponseTypeEnum.RADIO, compliance_weight=2, order_num=1)
    q2 = Question(group_id=group.id, text="Water active?", response_type=ResponseTypeEnum.RADIO, compliance_weight=3, order_num=2)
    q3 = Question(group_id=group.id, text="Soap dispenser?", response_type=ResponseTypeEnum.RADIO, compliance_weight=1, order_num=3)
    db.add_all([q1, q2, q3])
    db.commit()
    
    # 3. Create Audit Instance
    audit = Audit(
        template_id=template.id,
        department_id=dept.id,
        auditor_id=user.id,
        status=AuditStatusEnum.DRAFT,
        audited_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()
    
    # 4. Answers: Yes (Wt 2), No (Wt 3), NA (Wt 1 - Exclude)
    resp1 = AuditResponse(audit_id=audit.id, question_id=q1.id, answer="Yes", score=2.0)
    resp2 = AuditResponse(audit_id=audit.id, question_id=q2.id, answer="No", score=0.0)
    resp3 = AuditResponse(audit_id=audit.id, question_id=q3.id, answer="N/A", score=0.0)
    db.add_all([resp1, resp2, resp3])
    db.commit()
    
    # 5. Execute scoring calculation
    calculate_audit_scores(db, audit.id)
    
    # Reload from DB
    db.refresh(audit)
    
    # Total applicable weight = 2 (q1) + 3 (q2) = 5. (q3 is N/A, excluded)
    # Total earned score = 2 (q1 = Yes) + 0 (q2 = No) = 2.
    # Compliance score = (2 / 5) * 100% = 40.0%
    assert float(audit.compliance_percentage) == 40.0
    assert audit.risk_level == RiskLevelEnum.CRITICAL
