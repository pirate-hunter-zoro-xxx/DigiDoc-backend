from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from core.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash
    
    Args:
        plain_password: The plain text password
        hashed_password: The bcrypt hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash from a plain password
    
    Args:
        password: The plain text password
        
    Returns:
        The bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None, 
    user_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token with embedded user data (no DB query needed)
    
    Args:
        data: The data to encode in the token (sub, user_id)
        expires_delta: Optional custom expiration time
        user_data: Optional full user data to embed in token (name, role, is_active, organization_id)
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    # Embed user data in token to eliminate database queries
    if user_data:
        to_encode["name"] = user_data.get("name")
        to_encode["role"] = user_data.get("role", "user")
        to_encode["is_active"] = user_data.get("is_active", True)
        to_encode["organization_id"] = user_data.get("organization_id")
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], user_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: The data to encode in the token
        user_data: Optional user data to embed (role, organization_id)
        
    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    # Embed minimal user data for refresh tokens
    if user_data:
        to_encode["role"] = user_data.get("role", "user")
        to_encode["organization_id"] = user_data.get("organization_id")
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token
    
    Args:
        token: The JWT token to verify
        token_type: The expected token type ("access" or "refresh")
        
    Returns:
        The decoded token payload if valid (includes role), None otherwise
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Check if token type matches
        if payload.get("type") != token_type:
            return None
        
        # Role field is optional for backward compatibility during migration
        # but should be present in all new tokens
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without verification (use with caution)
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except JWTError:
        return None
