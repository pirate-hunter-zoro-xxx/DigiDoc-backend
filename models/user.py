from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(BaseModel):
    """Model for user registration"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Model for updating user profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class UserPasswordChange(BaseModel):
    """Model for changing user password"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    """Model for user response (public data)"""
    id: str
    email: str
    name: str
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(BaseModel):
    """Model for user as stored in database"""
    id: str
    email: str
    name: str
    password_hash: str
    created_at: str
    updated_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
