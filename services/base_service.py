"""
Base service class for consistent Supabase client usage across all services
"""
from abc import ABC
from typing import Optional
import logging

from core.database import get_supabase_client
from fastapi import HTTPException, status


logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Base class for all services
    
    Provides:
    - Consistent Supabase client initialization (singleton pattern)
    - Shared utility methods
    - Standard error handling patterns
    
    Usage:
        class MyService(BaseService):
            async def my_method(self):
                # Use self.supabase for all database operations
                result = self.supabase.table("users").select("*").execute()
    """
    
    def __init__(self):
        """Initialize service with Supabase client singleton"""
        self._supabase = get_supabase_client()
    
    @property
    def supabase(self):
        """
        Get Supabase client instance (singleton)
        
        Returns:
            Supabase client instance
        """
        return self._supabase
    
    def _handle_db_error(self, error: Exception, operation: str) -> None:
        """
        Standard error handling for database operations
        
        Args:
            error: The exception that occurred
            operation: Description of the operation (for logging)
            
        Raises:
            HTTPException: 500 Internal Server Error with details
        """
        logger.error(f"Database error in {operation}: {str(error)}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {operation}"
        )
    
    def _validate_required_fields(self, data: dict, required_fields: list) -> None:
        """
        Validate that required fields are present in data
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Raises:
            HTTPException: 400 Bad Request if fields missing
        """
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
