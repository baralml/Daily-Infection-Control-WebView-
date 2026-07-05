import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.security import get_password_hash, verify_password
from app.models.auth import User, Role, LoginHistory, AuditLog
from app.schemas.auth import UserCreate, UserUpdate, RoleCreate

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Fetch user by email address."""
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Fetch user by UUID."""
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """List users with offset pagination."""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, obj_in: UserCreate) -> User:
    """Create new hashed-password user in the database."""
    hashed_password = get_password_hash(obj_in.password)
    db_user = User(
        email=obj_in.email,
        hashed_password=hashed_password,
        full_name=obj_in.full_name,
        phone_number=obj_in.phone_number,
        role_id=obj_in.role_id,
        is_active=obj_in.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, obj_in: UserUpdate) -> User:
    """Update user attributes, including hashing new passwords if passed."""
    update_data = obj_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

# Role-specific CRUD helpers
def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()

def create_role(db: Session, obj_in: RoleCreate) -> Role:
    db_role = Role(
        name=obj_in.name,
        description=obj_in.description,
        permissions=obj_in.permissions
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_roles(db: Session) -> List[Role]:
    return db.query(Role).all()

# Login History helper
def create_login_record(db: Session, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str], status: str) -> LoginHistory:
    record = LoginHistory(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

# Audit Logs helper
def log_security_event(
    db: Session,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_name: Optional[str],
    entity_id: Optional[str],
    old_values: Optional[dict],
    new_values: Optional[dict],
    ip_address: str,
    user_agent: Optional[str]
) -> AuditLog:
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
