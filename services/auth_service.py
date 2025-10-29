from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from core.database import get_supabase_client
from core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from models.user import UserCreate, UserLogin, UserInDB, UserResponse
from models.token import AuthResponse


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def register_user(self, user_data: UserCreate) -> AuthResponse:
        """
        Register a new user
        
        Args:
            user_data: User registration data
            
        Returns:
            AuthResponse with user data and tokens
            
        Raises:
            HTTPException: If email already exists or registration fails
        """
        try:
            # Check if user already exists
            existing_user = self.supabase.table("users").select("*").eq("email", user_data.email).execute()
            
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash the password
            password_hash = get_password_hash(user_data.password)
            
            # Insert user into database
            new_user = self.supabase.table("users").insert({
                "email": user_data.email,
                "name": user_data.name,
                "password_hash": password_hash
            }).execute()
            
            if not new_user.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            user = new_user.data[0]
            
            # Create tokens
            access_token = create_access_token(
                data={"sub": user["email"], "user_id": str(user["id"])}
            )
            refresh_token = create_refresh_token(
                data={"sub": user["email"], "user_id": str(user["id"])}
            )
            
            user_response = {
                "id": str(user["id"]),
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"]
            }
            
            return AuthResponse(
                message="User registered successfully",
                user=user_response,
                access_token=access_token,
                refresh_token=refresh_token
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred: {str(e)}"
            )
    
    async def login_user(self, credentials: UserLogin) -> AuthResponse:
        """
        Authenticate a user and return tokens
        
        Args:
            credentials: User login credentials
            
        Returns:
            AuthResponse with user data and tokens
            
        Raises:
            HTTPException: If credentials are invalid
        """
        try:
            # Get user from database
            user_query = self.supabase.table("users").select("*").eq("email", credentials.email).execute()
            
            if not user_query.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            user = user_query.data[0]
            
            # Verify password
            if not verify_password(credentials.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Create tokens
            access_token = create_access_token(
                data={"sub": user["email"], "user_id": str(user["id"])}
            )
            refresh_token = create_refresh_token(
                data={"sub": user["email"], "user_id": str(user["id"])}
            )
            
            user_response = {
                "id": str(user["id"]),
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"]
            }
            
            return AuthResponse(
                message="Login successful",
                user=user_response,
                access_token=access_token,
                refresh_token=refresh_token
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred: {str(e)}"
            )
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Generate a new access token from a refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict with new access_token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        from core.security import verify_token
        
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": payload["sub"], "user_id": payload["user_id"]}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }


# Create service instance
auth_service = AuthService()
