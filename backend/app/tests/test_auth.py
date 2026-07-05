from app.core.security import verify_password, get_password_hash, create_access_token, decode_token
from app.models.auth import Role, User

def test_password_hashing():
    """Confirms bcrypt password encryption integrity."""
    password = "secretpassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_generation():
    """Validates JWT access token generation and claims decoding."""
    subject = "user-uuid-12345"
    token = create_access_token(subject)
    assert isinstance(token, str)
    
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == subject
    assert payload.get("type") == "access"

def test_auth_login_endpoints(client, db):
    """Tests registration logic and login authentication flow."""
    # Seed default role
    role = Role(
        name="SUPER ADMIN",
        description="super admin description",
        permissions={"modules": {"users": ["read", "write"]}}
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Create user directly
    hashed = get_password_hash("testpassword123")
    user = User(
        email="test@hospital.com",
        hashed_password=hashed,
        full_name="Dr. Test User",
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Test login request
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@hospital.com", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_info"]["email"] == "test@hospital.com"
    
    # Test login with invalid password
    bad_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@hospital.com", "password": "wrongpassword"}
    )
    assert bad_response.status_code == 400
