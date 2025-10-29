# Integration Guide

## How to Integrate Other Services with PPL Auth Service

This auth service is designed to work as a microservice that other services can integrate with for user authentication and management.

---

## Overview

**PPL Auth Service** handles:
- User registration
- User authentication (login)
- JWT token generation & validation
- User profile management
- Password management

**Your other services** (payments, billing, etc.) should:
- Validate JWT tokens
- Get user information from this service
- Not store or manage passwords

---

## Integration Patterns

### Pattern 1: JWT Token Validation (Recommended)

Your service validates the JWT token independently without calling the auth service.

#### Implementation:

**1. Share JWT Secret**
```python
# In your other service
JWT_SECRET_KEY = "same-secret-as-auth-service"
JWT_ALGORITHM = "HS256"
```

**2. Validate Token**
```python
from jose import JWTError, jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# Usage
user_data = verify_token(token_from_request)
if user_data:
    user_id = user_data["user_id"]
    user_email = user_data["sub"]
```

**✅ Pros:**
- Fast (no network call)
- Scalable
- Service remains independent

**❌ Cons:**
- Can't check if user was deleted
- Shared secret management

---

### Pattern 2: API Call to Auth Service

Your service calls the auth service to validate the user.

#### Implementation:

```python
import httpx

AUTH_SERVICE_URL = "http://localhost:8000/api/v1"

async def get_current_user(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTH_SERVICE_URL}/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        return None

# Usage in your FastAPI endpoint
@app.get("/payments/history")
async def get_payment_history(token: str = Header(...)):
    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Process payment history for user["id"]
    return get_payments(user["id"])
```

**✅ Pros:**
- Always up-to-date user info
- Can check if user exists/deleted
- Single source of truth

**❌ Cons:**
- Network latency
- Auth service becomes dependency
- More complex error handling

---

## Example: Payment Service Integration

### Scenario
You're building a payment service that needs to charge authenticated users.

### Architecture

```
Frontend
   ↓ (sends JWT token)
Payment Service
   ↓ (validates token OR calls auth service)
Auth Service
   ↓ (validates user)
Database
```

### Implementation

**payment_service.py:**
```python
from fastapi import FastAPI, Header, HTTPException
from jose import jwt
import os

app = FastAPI()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"

def verify_token(token: str):
    """Validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("sub")
        }
    except:
        return None

@app.post("/payments/create")
async def create_payment(
    amount: float,
    authorization: str = Header(...)
):
    # Extract token
    token = authorization.replace("Bearer ", "")
    
    # Validate user
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Process payment for user
    payment = process_payment(
        user_id=user["user_id"],
        amount=amount
    )
    
    return {"payment_id": payment.id, "status": "success"}
```

---

## Frontend Integration

### 1. Login and Store Tokens

```javascript
// Login
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();

// Store tokens
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### 2. Call Your Service with Token

```javascript
// Call payment service
const token = localStorage.getItem('access_token');

const response = await fetch('http://payment-service:8001/payments/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ amount: 99.99 })
});
```

### 3. Handle Token Refresh

```javascript
async function refreshToken() {
  const refresh_token = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
}

// Use axios interceptor or similar to auto-refresh on 401
```

---

## Docker Compose Example

Run multiple services together:

```yaml
version: '3.8'

services:
  auth-service:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    
  payment-service:
    build: ./payment-service
    ports:
      - "8001:8001"
    environment:
      - AUTH_SERVICE_URL=http://auth-service:8000
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - auth-service
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_AUTH_API=http://localhost:8000
      - NEXT_PUBLIC_PAYMENT_API=http://localhost:8001
```

---

## Security Best Practices

### 1. Token Transmission
- ✅ Always use HTTPS in production
- ✅ Send tokens in Authorization header (not URL)
- ✅ Never log tokens

### 2. Token Storage
- ✅ Use httpOnly cookies (preferred)
- ⚠️ localStorage (acceptable for development)
- ❌ Never store in URL or localStorage for sensitive apps

### 3. Token Validation
- ✅ Validate token signature
- ✅ Check expiration
- ✅ Verify token type (access vs refresh)

### 4. Secret Management
- ✅ Use environment variables
- ✅ Different secrets per environment
- ✅ Rotate secrets regularly
- ❌ Never commit secrets to git

---

## Testing Integration

### Test Token Generation

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "password123"
  }'

# Response includes access_token
```

### Test Token Validation in Your Service

```python
# test_payment_service.py
import pytest
from jose import jwt

def test_valid_token():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    user = verify_token(token)
    assert user is not None
    assert "user_id" in user
```

---

## Common Issues & Solutions

### Issue: 401 Unauthorized
**Cause:** Token expired or invalid
**Solution:** Implement token refresh logic

### Issue: CORS Error
**Cause:** Service not in CORS allowed origins
**Solution:** Add your service URL to `BACKEND_CORS_ORIGINS`

### Issue: Token validation fails
**Cause:** Different JWT secret keys
**Solution:** Ensure all services share the same `JWT_SECRET_KEY`

---

## Support

For questions or issues:
1. Check the API documentation: `/docs`
2. Review error logs
3. Verify environment variables
4. Test endpoints with Swagger UI

---

## Next Steps

1. ✅ Set up auth service
2. ✅ Test authentication flow
3. ✅ Implement token validation in your service
4. ✅ Add proper error handling
5. ✅ Deploy services
6. ✅ Monitor and log
