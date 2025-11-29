from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class OrganizationBase(BaseModel):
    """Base organization fields shared across models"""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., pattern=r'^[a-z0-9-]+$', description="URL-friendly identifier (lowercase, numbers, hyphens)")
    description: Optional[str] = Field(None, description="Optional organization description")


class OrganizationCreate(OrganizationBase):
    """
    Model for creating a new organization
    Only super admin can create organizations
    """
    pass


class OrganizationUpdate(BaseModel):
    """
    Model for updating organization fields
    All fields are optional for partial updates
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = Field(None, description="Active status of organization")


class OrganizationResponse(OrganizationBase):
    """
    Model for organization response
    Includes all database fields
    """
    id: str
    is_active: bool
    created_at: str
    updated_at: str
    created_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationWithStats(OrganizationResponse):
    """
    Extended organization model with statistics
    Used for admin dashboard and detailed views
    """
    user_count: int = Field(0, description="Total number of users in organization")
    active_user_count: int = Field(0, description="Number of active users")
    request_count: int = Field(0, description="Total number of requests")
    pending_request_count: int = Field(0, description="Number of pending/draft requests")


class OrganizationListResponse(BaseModel):
    """Model for paginated organization list"""
    data: list[OrganizationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [],
                "total": 10,
                "page": 1,
                "page_size": 50,
                "total_pages": 1
            }
        }
