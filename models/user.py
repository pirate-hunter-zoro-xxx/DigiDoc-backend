from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    """User role enum matching database enum"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.USER
    is_active: bool = True


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
    role: UserRole
    is_active: bool
    created_at: str
    last_login_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(BaseModel):
    """Model for user as stored in database"""
    id: str
    email: str
    name: str
    password_hash: str
    role: UserRole
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    last_login_at: Optional[str] = None
    updated_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# Admin-specific Models
# ============================================

class UserCreateByAdmin(BaseModel):
    """Model for admin creating users (can set role)"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER
    is_active: bool = True

    def validate_role_permission(self, admin_role: UserRole) -> bool:
        """
        Validate if admin has permission to create user with this role
        
        Args:
            admin_role: Role of the admin creating the user
            
        Returns:
            True if allowed, False otherwise
        """
        # No one can create super admin via API
        if self.role == UserRole.SUPER_ADMIN:
            return False
        
        # Only super admin can create other admins
        if self.role == UserRole.ADMIN and admin_role != UserRole.SUPER_ADMIN:
            return False
        
        return True

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "name": "New User",
                "password": "SecurePassword123",
                "role": "user",
                "is_active": True
            }
        }


class UserUpdateByAdmin(BaseModel):
    """Model for admin updating users"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    # Note: role updated via separate endpoint for security

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Name",
                "email": "updated@example.com",
                "is_active": True
            }
        }


class UserRoleUpdate(BaseModel):
    """Model for updating user role (super admin only)"""
    role: UserRole

    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin"
            }
        }


class UserStatusUpdate(BaseModel):
    """Model for activating/deactivating user"""
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "is_active": False
            }
        }


class UserListResponse(BaseModel):
    """Model for paginated user list"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "users": [],
                "total": 50,
                "page": 1,
                "page_size": 20,
                "total_pages": 3
            }
        }


class AdminStatsResponse(BaseModel):
    """Model for admin dashboard statistics"""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: Dict[str, int]
    total_requests: int
    pending_approvals: int
    recent_signups: int  # Last 7 days

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 150,
                "active_users": 145,
                "inactive_users": 5,
                "users_by_role": {
                    "user": 148,
                    "admin": 1,
                    "super_admin": 1
                },
                "total_requests": 1250,
                "pending_approvals": 23,
                "recent_signups": 12
            }
        }
