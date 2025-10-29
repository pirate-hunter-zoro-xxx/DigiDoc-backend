from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Model for token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Model for decoded token data"""
    email: Optional[str] = None
    user_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Model for refresh token request"""
    refresh_token: str


class AuthResponse(BaseModel):
    """Model for authentication response"""
    message: str
    user: dict
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
