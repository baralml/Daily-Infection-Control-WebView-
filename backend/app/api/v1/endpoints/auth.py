import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.crud.crud_user import get_user_by_email, create_login_record, log_security_event, get_user, create_user, get_roles
from app.schemas.auth import Token, UserResponse, UserCreate, RoleResponse
from app.models.auth import Role
from typing import List

import random
import redis
from pydantic import BaseModel, EmailStr

router = APIRouter()

redis_client = redis.from_url(settings.REDIS_URL)

class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

@router.post("/register/send-otp")
def send_register_otp(payload: SendOTPRequest) -> Any:
    """Generates a 6-digit verification OTP, logs it for reference, 
    and stores it in Redis for registration confirmation.
    """
    # Generate 6-digit OTP code
    otp_code = f"{random.randint(100000, 999999)}"
    
    # Store in Redis with a 5-minute expiry
    redis_client.setex(f"otp:{payload.email}", 300, otp_code)
    
    # Log it
    print(f"\n[REGISTRATION OTP] Email: {payload.email} | OTP Code: {otp_code}\n", flush=True)
    
    return {
        "message": f"Verification code sent to {payload.email}!",
        "mock_otp": otp_code  # Expose OTP in response for simplified UI testing
    }

@router.post("/register/verify-otp")
def verify_register_otp(payload: VerifyOTPRequest) -> Any:
    """Validates the submitted OTP against Redis cached keys."""
    cached_otp = redis_client.get(f"otp:{payload.email}")
    if not cached_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code expired or email not requested"
        )
    
    # Decode bytes from redis
    if isinstance(cached_otp, bytes):
        cached_otp = cached_otp.decode("utf-8")
        
    if cached_otp != payload.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification OTP code"
        )
        
    # Success! Clean up the OTP key
    redis_client.delete(f"otp:{payload.email}")
    return {"message": "Email verified successfully", "verified": True}

@router.get("/roles", response_model=List[RoleResponse])
def get_public_roles(db: Session = Depends(get_db)) -> Any:
    """Lists available user roles for registration selector."""
    return get_roles(db)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    request: Request,
    obj_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Public self-registration for staff. Accounts are disabled (is_active=False) 
    until approved by a System Admin.
    """
    db_user = get_user_by_email(db, email=obj_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
        
    role = db.query(Role).filter(Role.id == obj_in.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Designated role does not exist"
        )
        
    # Enforce inactive by default for admin approval
    obj_in.is_active = False
    new_user = create_user(db, obj_in)
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    log_security_event(
        db, new_user.id, "USER_SELF_REGISTERED", "users", str(new_user.id),
        None, {"email": new_user.email, "role": role.name, "is_active": False},
        client_ip, user_agent
    )
    return new_user

@router.post("/login", response_model=Token)
def login(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login. Yields JWT access token 
    and writes an HttpOnly Refresh cookie.
    """
    user = get_user_by_email(db, email=form_data.username)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        if user:
            create_login_record(db, user.id, client_ip, user_agent, "FAILED")
            log_security_event(db, user.id, "LOGIN_FAILED", "users", str(user.id), None, None, client_ip, user_agent)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    if not user.is_active:
        create_login_record(db, user.id, client_ip, user_agent, "FAILED_INACTIVE")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Generate credentials
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Store history
    create_login_record(db, user.id, client_ip, user_agent, "SUCCESS")
    log_security_event(db, user.id, "LOGIN_SUCCESS", "users", str(user.id), None, None, client_ip, user_agent)
    
    # Write HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.MINIO_SECURE,  # use HTTPS/secure in production
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": user
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    refresh_token: str = Cookie(None)
) -> Any:
    """Rotates refresh cookie to supply a new JWT access token."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token cookie missing"
        )
        
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
        
    user_id_str = payload.get("sub")
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject uuid"
        )
        
    user = get_user(db, user_uuid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )
        
    # Rotate Tokens
    new_access = create_access_token(subject=user.id)
    new_refresh = create_refresh_token(subject=user.id)
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=settings.MINIO_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    
    log_security_event(db, user.id, "TOKEN_REFRESHED", "users", str(user.id), None, None, client_ip, user_agent)
    
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "user_info": user
    }

@router.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db), refresh_token: str = Cookie(None)) -> Any:
    """Clears HTTP sessions and invalidates cookies."""
    if refresh_token:
        payload = decode_token(refresh_token)
        if payload:
            user_id = payload.get("sub")
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            try:
                user_uuid = uuid.UUID(user_id)
                log_security_event(db, user_uuid, "LOGOUT", "users", str(user_uuid), None, None, client_ip, user_agent)
            except ValueError:
                pass
                
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}
