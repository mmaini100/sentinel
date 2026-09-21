"""
Auth API router.

POST /auth/login — authenticate and return JWT token
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Mock login endpoint. 
    Accepts any email and password 'admin', returns a JWT with admin role.
    """
    if request.password != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials. Use password 'admin'.")

    now = datetime.now(timezone.utc)
    # Long expiry for demo purposes
    expires = now + timedelta(days=1)
    
    user_payload = {
        "sub": str(request.email),
        "role": "admin",
        "name": request.email.split("@")[0].capitalize(),
    }
    
    token_payload = {
        **user_payload,
        "iat": now,
        "exp": expires,
    }
    
    token = jwt.encode(token_payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    
    return LoginResponse(
        access_token=token,
        user=user_payload,
    )
