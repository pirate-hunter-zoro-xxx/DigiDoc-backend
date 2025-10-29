"""
Requests API Endpoints
"""
from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from core.dependencies import get_current_active_user
from models.user import UserResponse
from models.request import (
    RequestCreate, RequestUpdate, RequestResponse, RequestDetailResponse,
    RequestListResponse, RequestStatus, CommentCreate, CommentResponse
)
from services.request_service import RequestService

router = APIRouter()


@router.post(
    "",
    response_model=RequestDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new request",
    description="Create a new request with optional workflow stages. Request starts in DRAFT status."
)
async def create_request(
    request_data: RequestCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Create a new request
    
    - **title**: Title of the request (required, 3-255 characters)
    - **description**: Detailed description (optional)
    - **workflow_stages**: List of workflow stages with recommenders and approvers
    
    Returns the created request with workflow stages.
    """
    service = RequestService()
    return await service.create_request(request_data, current_user.id)


@router.get(
    "",
    response_model=RequestListResponse,
    summary="List requests",
    description="Get list of requests created by or assigned to the current user"
)
async def list_requests(
    status_filter: Optional[RequestStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    created_by_me: bool = Query(True, description="Show only requests created by me (default: true)"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    List all requests for the current user
    
    - Shows requests created by the user (when created_by_me=true)
    - Shows all requests including assigned ones (when created_by_me=false)
    - Supports pagination and status filtering
    """
    service = RequestService()
    return await service.list_user_requests(
        current_user.id,
        status_filter,
        page,
        page_size,
        created_by_me
    )


@router.get(
    "/{request_id}",
    response_model=RequestDetailResponse,
    summary="Get request details",
    description="Get detailed information about a specific request including workflow stages"
)
async def get_request(
    request_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get request by ID
    
    - Returns full request details
    - Includes all workflow stages with current status
    - Includes user permissions (can_edit, can_submit, can_cancel)
    """
    service = RequestService()
    return await service.get_request(request_id, current_user.id)


@router.put(
    "/{request_id}",
    response_model=RequestDetailResponse,
    summary="Update request",
    description="Update request details. Only allowed for DRAFT requests by the creator."
)
async def update_request(
    request_id: str,
    update_data: RequestUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Update a request
    
    - Only creator can update
    - Only DRAFT requests can be updated
    - Can update title and/or description
    """
    service = RequestService()
    return await service.update_request(request_id, current_user.id, update_data)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete request",
    description="Delete a request. Only allowed for DRAFT requests by the creator."
)
async def delete_request(
    request_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Delete a request
    
    - Only creator can delete
    - Only DRAFT requests can be deleted
    - Cascade deletes workflow stages
    """
    service = RequestService()
    return await service.delete_request(request_id, current_user.id)


@router.post(
    "/{request_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add a comment to a request"
)
async def add_comment(
    request_id: str,
    comment_data: CommentCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Add a comment to a request
    
    - Available to creator and workflow participants
    - Useful for discussion and clarification
    """
    service = RequestService()
    return await service.add_comment(request_id, current_user.id, comment_data)


@router.get(
    "/{request_id}/comments",
    response_model=list[CommentResponse],
    summary="Get comments",
    description="Get all comments for a request"
)
async def get_comments(
    request_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get all comments for a request
    
    - Returns comments in chronological order
    - Includes commenter information
    """
    service = RequestService()
    return await service.get_comments(request_id, current_user.id)
