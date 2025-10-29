from fastapi import APIRouter, status
from models.user import UserCreate, UserLogin
from models.token import AuthResponse, RefreshTokenRequest
from services.auth_service import auth_service

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user
    
    - **email**: Valid email address
    - **name**: User's full name
    - **password**: Password (minimum 6 characters)
    
    Returns user data with access and refresh tokens
    """
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin):
    """
    Login user and receive authentication tokens
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns user data with access and refresh tokens
    """
    return await auth_service.login_user(credentials)


@router.post("/refresh")
async def refresh_token(token_request: RefreshTokenRequest):
    """
    Refresh access token using a valid refresh token
    
    - **refresh_token**: Valid refresh token from login/register
    
    Returns a new access token
    """
    return await auth_service.refresh_access_token(token_request.refresh_token)


@router.post("/logout")
async def logout():
    """
    Logout user (client should delete tokens)
    
    Note: Since we're using stateless JWT, actual logout is handled client-side
    by deleting the tokens. This endpoint exists for API consistency.
    """
    return {"message": "Logout successful. Please delete your tokens."}
