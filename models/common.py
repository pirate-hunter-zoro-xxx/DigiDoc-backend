"""
Common response models for standardized API responses
"""
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized paginated response format
    
    Usage:
        @router.get("/users", response_model=PaginatedResponse[UserResponse])
        async def list_users():
            return PaginatedResponse(
                data=[...],
                total=100,
                page=1,
                page_size=10
            )
    """
    data: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10
            }
        }
