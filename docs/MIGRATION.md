# Migration Guide: Monolithic → Modular Architecture

This guide helps you understand the changes and migrate your code to the new modular structure.

## 📋 Table of Contents

1. [Overview](#overview)
2. [What Changed](#what-changed)
3. [File Mapping](#file-mapping)
4. [API Changes](#api-changes)
5. [Code Migration](#code-migration)
6. [Testing Migration](#testing-migration)
7. [Rollback Plan](#rollback-plan)

---

## Overview

We've refactored the backend from a monolithic structure to a modular microservice architecture. The old code still exists as backups, and backward compatibility routes ensure existing frontends continue working.

### Benefits
- ✅ Better code organization
- ✅ Easier to test individual components
- ✅ Simpler to add new features
- ✅ Ready for microservices architecture
- ✅ API versioning support

### Backward Compatibility
Your existing frontend will work without changes! Legacy routes `/api/register` and `/api/login` still function.

---

## What Changed

### Before (Monolithic)
```
backend/
├── main.py          # All routes and logic
├── auth.py          # JWT and password utils
├── database.py      # Supabase client
└── requirements.txt
```

### After (Modular)
```
backend/
├── main.py                    # App initialization only
├── core/
│   ├── config.py             # Centralized configuration
│   ├── security.py           # JWT & password hashing
│   ├── database.py           # Supabase client
│   └── dependencies.py       # Auth dependencies
├── api/v1/
│   ├── router.py             # Main router
│   └── endpoints/
│       ├── auth.py           # Auth routes
│       ├── users.py          # User routes
│       └── health.py         # Health checks
├── models/
│   ├── user.py               # User schemas
│   └── token.py              # Token schemas
├── services/
│   ├── auth_service.py       # Auth business logic
│   └── user_service.py       # User business logic
└── schemas/
    └── users.sql             # Database schema
```

---

## File Mapping

### Old → New Locations

| Old File | New Location | Changes |
|----------|--------------|---------|
| `main.py` (routes) | `api/v1/endpoints/auth.py` | Routes split into auth, users, health |
| `main.py` (logic) | `services/auth_service.py`, `services/user_service.py` | Business logic separated |
| `auth.py` | `core/security.py` | Enhanced with refresh tokens |
| `database.py` | `core/database.py` | Added singleton pattern |
| N/A | `core/config.py` | New: centralized settings |
| N/A | `core/dependencies.py` | New: FastAPI dependencies |
| N/A | `models/user.py`, `models/token.py` | New: Pydantic models |

### Backup Files Created
- `main.py.backup` - Original main.py
- `auth.py.old` - Original auth.py
- `database.py.old` - Original database.py

---

## API Changes

### New Endpoint Structure

| Old Endpoint | New Endpoint | Status |
|--------------|--------------|--------|
| `POST /api/register` | `POST /api/v1/auth/register` | ✅ Both work |
| `POST /api/login` | `POST /api/v1/auth/login` | ✅ Both work |
| N/A | `POST /api/v1/auth/refresh` | ✅ New |
| N/A | `POST /api/v1/auth/logout` | ✅ New |
| N/A | `GET /api/v1/users/me` | ✅ New |
| N/A | `PUT /api/v1/users/me` | ✅ New |
| N/A | `PATCH /api/v1/users/me/password` | ✅ New |
| N/A | `DELETE /api/v1/users/me` | ✅ New |
| N/A | `GET /api/v1/health/health` | ✅ New |
| N/A | `GET /api/v1/health/ready` | ✅ New |

### Response Format Changes

#### Old Register/Login Response
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

#### New Response (v1 endpoints)
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Note**: Legacy endpoints (`/api/register`, `/api/login`) return the old format for backward compatibility.

---

## Code Migration

### 1. Import Changes

#### Old Code
```python
from auth import hash_password, verify_password, create_access_token
from database import get_supabase_client
```

#### New Code
```python
from core.security import get_password_hash, verify_password, create_access_token
from core.database import get_supabase_client
```

### 2. Configuration Access

#### Old Code
```python
import os
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
```

#### New Code
```python
from core.config import get_settings

settings = get_settings()
JWT_SECRET = settings.JWT_SECRET_KEY
```

### 3. Using Services

#### Old Code (Inline Logic)
```python
@app.post("/api/register")
async def register(user: UserCreate):
    # Hash password
    hashed = hash_password(user.password)
    
    # Insert into database
    supabase = get_supabase_client()
    result = supabase.table("users").insert({
        "email": user.email,
        "password_hash": hashed,
        "name": user.name
    }).execute()
    
    # Create token
    token = create_access_token({"sub": result.data[0]["id"]})
    
    return {"token": token, "user": result.data[0]}
```

#### New Code (Using Services)
```python
from services.auth_service import register_user
from models.user import UserCreate

@router.post("/register")
async def register(user: UserCreate):
    auth_response = await register_user(user)
    return auth_response
```

### 4. Protected Routes

#### Old Code
```python
@app.get("/api/profile")
async def get_profile(token: str = Header()):
    # Manual token validation
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    # Fetch user
    supabase = get_supabase_client()
    result = supabase.table("users").select("*").eq("id", user_id).execute()
    
    return result.data[0]
```

#### New Code
```python
from core.dependencies import get_current_active_user
from models.user import UserResponse

@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: UserResponse = Depends(get_current_active_user)):
    return current_user
```

---

## Testing Migration

### Unit Test Example

#### Old Test
```python
def test_hash_password():
    from auth import hash_password
    hashed = hash_password("password123")
    assert hashed != "password123"
    assert len(hashed) > 50
```

#### New Test
```python
def test_hash_password():
    from core.security import get_password_hash
    hashed = get_password_hash("password123")
    assert hashed != "password123"
    assert len(hashed) > 50
```

### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "name": "Test User"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

def test_legacy_endpoint():
    """Test backward compatibility"""
    response = client.post("/api/register", json={
        "email": "legacy@example.com",
        "password": "SecurePass123!",
        "name": "Legacy User"
    })
    assert response.status_code == 200
    # Legacy format
    assert "access_token" in response.json()
    assert "token_type" in response.json()
```

---

## Frontend Migration

### Option 1: Keep Using Legacy Endpoints (Recommended Initially)

No changes needed! Your current frontend will work:

```typescript
// This still works
const response = await fetch('http://localhost:8000/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```

### Option 2: Migrate to New Endpoints (Recommended Long-term)

#### Before
```typescript
const response = await fetch('http://localhost:8000/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();
// { access_token, token_type, user }
localStorage.setItem('token', data.access_token);
```

#### After
```typescript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();
// { user, access_token, refresh_token, token_type }
localStorage.setItem('accessToken', data.access_token);
localStorage.setItem('refreshToken', data.refresh_token);
```

### New Feature: Token Refresh

```typescript
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refreshToken');
  
  const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  const data = await response.json();
  localStorage.setItem('accessToken', data.access_token);
  return data.access_token;
}

// Use in API calls
async function fetchProtectedResource() {
  let token = localStorage.getItem('accessToken');
  
  let response = await fetch('http://localhost:8000/api/v1/users/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (response.status === 401) {
    // Token expired, refresh it
    token = await refreshAccessToken();
    
    // Retry with new token
    response = await fetch('http://localhost:8000/api/v1/users/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }
  
  return response.json();
}
```

---

## Environment Variables Migration

### Old .env
```env
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=your-key
JWT_SECRET_KEY=your-secret
```

### New .env (Add These)
```env
# Existing (no changes)
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=your-key
JWT_SECRET_KEY=your-secret

# New (optional, have defaults)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000,https://yourapp.com
API_V1_PREFIX=/api/v1
DEBUG=True
```

---

## Rollback Plan

If you need to revert to the old version:

### Quick Rollback
```bash
cd backend

# Stop the server (Ctrl+C)

# Restore old files
cp main.py.backup main.py
cp auth.py.old auth.py
cp database.py.old database.py

# Restart server
uvicorn main:app --reload
```

### Complete Rollback (Git)
```bash
git checkout HEAD~1 backend/
```

---

## Verification Checklist

After migration, verify:

- [ ] Server starts without errors
- [ ] `/docs` page loads correctly
- [ ] Legacy endpoint `/api/register` works
- [ ] Legacy endpoint `/api/login` works
- [ ] New endpoint `/api/v1/auth/register` works
- [ ] New endpoint `/api/v1/auth/login` works
- [ ] Protected endpoints require authentication
- [ ] Health check `/api/v1/health/health` works
- [ ] Database connection works (`/api/v1/health/ready`)
- [ ] Existing frontend still functions
- [ ] Token refresh works (if migrated)

### Test Commands

```bash
# Test legacy register
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test User"}'

# Test new register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@example.com","password":"Test123!","name":"Test User 2"}'

# Test health check
curl http://localhost:8000/api/v1/health/health

# Test protected endpoint (replace TOKEN)
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer TOKEN"
```

---

## Common Migration Issues

### Issue 1: Import Errors
**Error**: `ModuleNotFoundError: No module named 'core'`

**Solution**: Make sure you're in the correct directory
```bash
cd backend
python -m pip install -r requirements.txt
```

### Issue 2: Missing pydantic-settings
**Error**: `ImportError: cannot import name 'BaseSettings'`

**Solution**: Install new dependency
```bash
pip install pydantic-settings==2.11.0
```

### Issue 3: Existing Frontend Not Working
**Symptom**: Login/register fails with new backend

**Solution**: Check backward compatibility routes are working
```bash
# Should return 200
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"existing@user.com","password":"password"}'
```

If this fails, check `main.py` has the legacy routes (lines ~70-100).

### Issue 4: Database Connection Errors
**Error**: Database queries fail

**Solution**: Verify Supabase credentials in `.env`
```bash
# Test connection
curl http://localhost:8000/api/v1/health/ready
```

---

## Next Steps

1. **Test Thoroughly**: Run all test cases
2. **Update Documentation**: Document any custom changes
3. **Monitor Logs**: Watch for errors in production
4. **Gradual Migration**: Move frontend to v1 endpoints gradually
5. **Deprecation Plan**: Eventually remove legacy routes

## Support

- Check [API.md](./API.md) for endpoint reference
- See [INTEGRATION.md](./INTEGRATION.md) for microservice integration
- Review [../README.md](../README.md) for setup help

---

**Migration complete!** 🎉 Your backend is now modular and ready for scaling.
