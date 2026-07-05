import uuid
from typing import List, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, PermissionChecker
from app.models.auth import User, Role
from app.crud.crud_user import get_users, get_user, create_user, update_user, log_security_event, get_roles
from app.schemas.auth import UserResponse, UserCreate, UserUpdate, RoleResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Returns the profile metadata of the current authenticated session."""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_my_profile(
    obj_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Allows the current user to update their own profile details (e.g. name, phone, password)."""
    update_data = obj_in.model_dump(exclude_unset=True)
    if "is_active" in update_data:
        del update_data["is_active"]
    if "role_id" in update_data:
        del update_data["role_id"]
        
    clean_in = UserUpdate(**update_data)
    return update_user(db, current_user, clean_in)

@router.get("", response_model=List[UserResponse])
def list_system_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _current_user: User = Depends(PermissionChecker("users", "read"))
) -> List[User]:
    """Admin endpoint to list all system users."""
    return get_users(db, skip=skip, limit=limit)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_new_user(
    request: Request,
    obj_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("users", "write"))
) -> User:
    """Admin endpoint to register a new user with designated role access."""
    # Check if role exists
    role = db.query(Role).filter(Role.id == obj_in.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role ID does not exist"
        )
        
    db_user = db.query(User).filter(User.email == obj_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
        
    new_user = create_user(db, obj_in)
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    log_security_event(
        db, current_user.id, "USER_CREATED", "users", str(new_user.id),
        None, {"email": new_user.email, "role": role.name}, client_ip, user_agent
    )
    
    return new_user

@router.put("/{user_id}", response_model=UserResponse)
def edit_user_details(
    user_id: uuid.UUID,
    request: Request,
    obj_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("users", "write"))
) -> User:
    """Admin endpoint to update user roles, active statuses, or profiles."""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    old_values = {"email": db_user.email, "role_id": db_user.role_id, "is_active": db_user.is_active}
    updated = update_user(db, db_user, obj_in)
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    log_security_event(
        db, current_user.id, "USER_UPDATED", "users", str(user_id),
        old_values, {"email": updated.email, "role_id": updated.role_id, "is_active": updated.is_active},
        client_ip, user_agent
    )
    
    return updated

@router.get("/roles", response_model=List[RoleResponse])
def list_system_roles(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> List[Role]:
    """Retrieve roles list for form selection in user administration."""
    return get_roles(db)

from app.models.capa import Notification

@router.get("/me/notifications", response_model=List[Any])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve in-app notifications for the logged-in user."""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "channel": n.channel,
            "is_read": n.is_read,
            "created_at": n.created_at
        }
        for n in notifications
    ]

@router.post("/me/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    n.read_at = datetime.utcnow()
    db.commit()
    return {"message": "Notification marked as read"}
