import uuid
from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import decode_token
from app.core.config import settings
from app.models.auth import User, Role

# OAuth2 scheme instance pointing to token URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """FastAPI dependency to extract JWT token, validate signature,
    verify active state, and return the database User model.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if not payload:
        raise credentials_exception
        
    user_id_str: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id_str is None or token_type != "access":
        raise credentials_exception
        
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user

class PermissionChecker:
    """FastAPI dependency class that checks if the logged-in user
    possesses permission for a module and action.
    """
    def __init__(self, module: str, action: str):
        self.module = module
        self.action = action

    def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Super Admin bypasses all checks
        if current_user.role.name.upper() == "SUPER ADMIN":
            return current_user
            
        role_permissions = current_user.role.permissions
        if not role_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permissions assigned to this role"
            )
            
        # Structure format: {"modules": {"audits": ["read", "write"]}} or simply {"audits": ["read", "write"]}
        modules_perm = role_permissions.get("modules", role_permissions)
        allowed_actions = modules_perm.get(self.module, [])
        
        if self.action not in allowed_actions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Module '{self.module}' action '{self.action}' is required."
            )
            
        return current_user
