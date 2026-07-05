import uuid
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.audit import Audit, AuditResponse, Question, QuestionGroup, AuditStatusEnum, RiskLevelEnum
from app.models.capa import Capa, CapaStatusEnum
from app.models.auth import User
from app.crud.crud_capa import create_capa
from app.schemas.capa import CapaCreate

def calculate_audit_scores(db: Session, audit_id: uuid.UUID) -> Audit:
    """Calculates Group Scores, Overall Score, Compliance Percentage, 
    and determines the Risk Level of the audit. Updates the DB audit record.
    """
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise ValueError("Audit not found")
        
    responses = db.query(AuditResponse).filter(AuditResponse.audit_id == audit_id).all()
    if not responses:
        # Defaults if no responses yet
        audit.overall_score = 0.00
        audit.compliance_percentage = 0.00
        audit.risk_level = RiskLevelEnum.LOW
        db.commit()
        db.refresh(audit)
        return audit

    # Build group-wise response dictionary
    # group_id -> list of (response_score, question_weight, is_applicable)
    group_data = {}
    total_earned = 0.0
    total_weight = 0.0
    
    for resp in responses:
        question = db.query(Question).filter(Question.id == resp.question_id).first()
        if not question:
            continue
            
        group_id = question.group_id
        weight = question.compliance_weight
        answer_upper = resp.answer.upper()
        
        is_applicable = answer_upper not in ["N/A", "NA", "NOT APPLICABLE"]
        
        if is_applicable:
            score = float(resp.score)  # Yes = weight, No = 0
            if group_id not in group_data:
                group_data[group_id] = []
            group_data[group_id].append((score, weight))
            
            total_earned += score
            total_weight += weight

    # Calculate group-wise scores and compile overall average
    group_scores = []
    for g_id, q_list in group_data.items():
        g_earned = sum(item[0] for item in q_list)
        g_weight = sum(item[1] for item in q_list)
        if g_weight > 0:
            g_score = (g_earned / g_weight) * 100.0
            group_scores.append(g_score)

    overall_score = sum(group_scores) / len(group_scores) if group_scores else 0.0
    compliance_pct = (total_earned / total_weight) * 100.0 if total_weight > 0 else 0.0

    # Risk level determination based on compliance percentage
    if compliance_pct >= 90.0:
        risk_level = RiskLevelEnum.LOW
    elif compliance_pct >= 75.0:
        risk_level = RiskLevelEnum.MEDIUM
    elif compliance_pct >= 50.0:
        risk_level = RiskLevelEnum.HIGH
    else:
        risk_level = RiskLevelEnum.CRITICAL

    audit.overall_score = round(overall_score, 2)
    audit.compliance_percentage = round(compliance_pct, 2)
    audit.risk_level = risk_level
    audit.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(audit)
    return audit

def auto_generate_capas(db: Session, audit_id: uuid.UUID, creator_id: uuid.UUID) -> int:
    """Scan audit responses and generate PENDING CAPA tickets for any 'No' answer."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        return 0

    responses = db.query(AuditResponse).filter(AuditResponse.audit_id == audit_id).all()
    capas_created = 0

    # Locate default assignee (nursing superintendent, department head, or ICO)
    # For robust defaults, we pick the auditor or search for a user with the corresponding dept role.
    # We will search for a user in the same department who is a Doctor In Charge, ICU/OT Head or similar.
    # If not found, default assignee is the auditor.
    default_assignee_id = audit.auditor_id
    dept_users = db.query(User).filter(User.is_active == True).all()
    # Choose first active user matching role or department if available, else auditor.
    
    for resp in responses:
        if resp.answer.upper() in ["NO", "N", "FALSE"]:
            question = db.query(Question).filter(Question.id == resp.question_id).first()
            if not question:
                continue

            # Check if CAPA already exists for this audit response to prevent duplicate generation
            existing_capa = db.query(Capa).filter(
                Capa.audit_id == audit_id,
                Capa.question_id == resp.question_id
            ).first()
            if existing_capa:
                continue

            # Map question weight to severity priority
            # weight >= 3 => High/Critical, weight == 2 => Medium, weight <= 1 => Low
            q_weight = question.compliance_weight
            priority = RiskLevelEnum.MEDIUM
            if q_weight >= 3:
                priority = RiskLevelEnum.HIGH
            elif q_weight <= 1:
                priority = RiskLevelEnum.LOW

            # Set deadline 7 days out
            deadline_date = date.today() + timedelta(days=7)

            title = f"Non-Conformance: {question.text[:60]}"
            if len(question.text) > 60:
                title += "..."

            description = (
                f"A non-conformance was identified during the audit "
                f"'{audit.template.title}' in department '{audit.department.name}' "
                f"on {audit.audited_at.strftime('%Y-%m-%d')}.\n\n"
                f"Audit Question: {question.text}\n"
                f"Auditor Remarks: {resp.remarks or 'No remarks provided.'}"
            )

            capa_in = CapaCreate(
                audit_id=audit_id,
                question_id=resp.question_id,
                department_id=audit.department_id,
                assigned_to=default_assignee_id,
                title=title,
                description=description,
                deadline=deadline_date,
                priority=priority,
                status=CapaStatusEnum.PENDING
            )

            create_capa(db, capa_in, creator_id)
            capas_created += 1

    return capas_created
