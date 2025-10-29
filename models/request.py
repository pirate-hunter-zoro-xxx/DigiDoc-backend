"""
Request and Workflow Models for Process Flow Application
"""
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, UUID4


# ============================================
# Enums
# ============================================

class RequestStatus(str, Enum):
    """Status of a request throughout its lifecycle"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    IN_APPROVAL = "IN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class StageType(str, Enum):
    """Type of workflow stage"""
    RECOMMEND = "RECOMMEND"
    APPROVE = "APPROVE"


class StageStatus(str, Enum):
    """Status of a workflow stage"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class StageAction(str, Enum):
    """Action taken on a workflow stage"""
    RECOMMENDED = "RECOMMENDED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ============================================
# Workflow Stage Models
# ============================================

class WorkflowStageCreate(BaseModel):
    """Schema for creating a workflow stage"""
    stage_type: StageType
    assigned_user_id: str
    order_index: int = Field(..., gt=0, description="Order in workflow (1, 2, 3...)")

    class Config:
        json_schema_extra = {
            "example": {
                "stage_type": "RECOMMEND",
                "assigned_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "order_index": 1
            }
        }


class WorkflowStageUpdate(BaseModel):
    """Schema for updating a workflow stage (taking action)"""
    action: StageAction
    comments: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "action": "RECOMMENDED",
                "comments": "Looks good, approved from technical perspective"
            }
        }


class WorkflowStageResponse(BaseModel):
    """Schema for workflow stage response"""
    id: str
    request_id: str
    stage_type: StageType
    assigned_user_id: str
    assigned_user_name: str
    assigned_user_email: str
    order_index: int
    status: StageStatus
    comments: Optional[str] = None
    action: Optional[StageAction] = None
    action_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "request_id": "123e4567-e89b-12d3-a456-426614174001",
                "stage_type": "RECOMMEND",
                "assigned_user_id": "123e4567-e89b-12d3-a456-426614174002",
                "assigned_user_name": "John Doe",
                "assigned_user_email": "john@example.com",
                "order_index": 1,
                "status": "COMPLETED",
                "comments": "Approved from technical perspective",
                "action": "RECOMMENDED",
                "action_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T09:00:00Z"
            }
        }


# ============================================
# Request Models
# ============================================

class RequestCreate(BaseModel):
    """Schema for creating a new request"""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    workflow_stages: List[WorkflowStageCreate] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Purchase New Development Laptop",
                "description": "Need MacBook Pro 16\" M3 for React development work",
                "workflow_stages": [
                    {
                        "stage_type": "RECOMMEND",
                        "assigned_user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "order_index": 1
                    },
                    {
                        "stage_type": "APPROVE",
                        "assigned_user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "order_index": 2
                    }
                ]
            }
        }


class RequestUpdate(BaseModel):
    """Schema for updating a request (only allowed in DRAFT status)"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Request Title",
                "description": "Updated description with more details"
            }
        }


class RequestResponse(BaseModel):
    """Schema for request response (without workflow stages)"""
    id: str
    title: str
    description: Optional[str] = None
    creator_id: str
    creator_name: str
    creator_email: str
    status: RequestStatus
    current_stage_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Purchase New Development Laptop",
                "description": "Need MacBook Pro 16\" M3",
                "creator_id": "123e4567-e89b-12d3-a456-426614174001",
                "creator_name": "Jane Smith",
                "creator_email": "jane@example.com",
                "status": "IN_REVIEW",
                "current_stage_id": "123e4567-e89b-12d3-a456-426614174002",
                "created_at": "2024-01-15T09:00:00Z",
                "updated_at": "2024-01-15T09:30:00Z",
                "submitted_at": "2024-01-15T09:30:00Z",
                "completed_at": None
            }
        }


class RequestDetailResponse(RequestResponse):
    """Schema for detailed request response (includes workflow stages)"""
    workflow_stages: List[WorkflowStageResponse] = Field(default_factory=list)
    can_edit: bool = False
    can_submit: bool = False
    can_cancel: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Purchase New Development Laptop",
                "description": "Need MacBook Pro 16\" M3",
                "creator_id": "123e4567-e89b-12d3-a456-426614174001",
                "creator_name": "Jane Smith",
                "creator_email": "jane@example.com",
                "status": "IN_REVIEW",
                "current_stage_id": "123e4567-e89b-12d3-a456-426614174002",
                "created_at": "2024-01-15T09:00:00Z",
                "updated_at": "2024-01-15T09:30:00Z",
                "submitted_at": "2024-01-15T09:30:00Z",
                "completed_at": None,
                "workflow_stages": [],
                "can_edit": False,
                "can_submit": False,
                "can_cancel": True
            }
        }


class RequestListResponse(BaseModel):
    """Schema for paginated request list response"""
    requests: List[RequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "requests": [],
                "total": 50,
                "page": 1,
                "page_size": 10,
                "total_pages": 5
            }
        }


# ============================================
# Request Action Models
# ============================================

class RequestSubmitResponse(BaseModel):
    """Response after submitting a request"""
    message: str
    request_id: str
    status: RequestStatus
    next_stage: Optional[WorkflowStageResponse] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Request submitted successfully",
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "SUBMITTED",
                "next_stage": None
            }
        }


class RequestCancelResponse(BaseModel):
    """Response after cancelling a request"""
    message: str
    request_id: str
    status: RequestStatus

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Request cancelled successfully",
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "CANCELLED"
            }
        }


# ============================================
# Comment Models
# ============================================

class CommentCreate(BaseModel):
    """Schema for creating a comment"""
    comment: str = Field(..., min_length=1, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "comment": "When do you need this laptop? Is it urgent?"
            }
        }


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: str
    request_id: str
    user_id: str
    user_name: str
    user_email: str
    comment: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "request_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "user_name": "John Doe",
                "user_email": "john@example.com",
                "comment": "When do you need this laptop?",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        }


# ============================================
# Pending Actions Models
# ============================================

class PendingActionResponse(BaseModel):
    """Schema for pending action item"""
    stage_id: str
    request_id: str
    request_title: str
    request_description: Optional[str]
    creator_name: str
    creator_email: str
    stage_type: StageType
    order_index: int
    submitted_at: Optional[datetime]
    days_pending: int

    class Config:
        json_schema_extra = {
            "example": {
                "stage_id": "123e4567-e89b-12d3-a456-426614174000",
                "request_id": "123e4567-e89b-12d3-a456-426614174001",
                "request_title": "Purchase New Laptop",
                "request_description": "Need MacBook Pro 16\" M3",
                "creator_name": "Jane Smith",
                "creator_email": "jane@example.com",
                "stage_type": "RECOMMEND",
                "order_index": 1,
                "submitted_at": "2024-01-15T09:00:00Z",
                "days_pending": 2
            }
        }


class PendingActionsListResponse(BaseModel):
    """Schema for list of pending actions"""
    pending_actions: List[PendingActionResponse]
    total_pending: int
    recommendations_pending: int
    approvals_pending: int

    class Config:
        json_schema_extra = {
            "example": {
                "pending_actions": [],
                "total_pending": 5,
                "recommendations_pending": 3,
                "approvals_pending": 2
            }
        }
