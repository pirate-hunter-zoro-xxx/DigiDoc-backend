# API Documentation

## PPL Auth Service API v1

Base URL: `http://localhost:8000/api/v1`

---

## Authentication Endpoints

### POST `/api/v1/auth/register`
Register a new user

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2025-10-25T10:00:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### POST `/api/v1/auth/login`
Login existing user

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2025-10-25T10:00:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### POST `/api/v1/auth/refresh`
Refresh access token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### POST `/api/v1/auth/logout`
Logout user

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Logout successful. Please delete your tokens."
}
```

---

## User Management Endpoints

### GET `/api/v1/users/me`
Get current user profile

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2025-10-25T10:00:00Z"
}
```

---

### PUT `/api/v1/users/me`
Update current user profile

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid-here",
  "email": "newemail@example.com",
  "name": "Jane Doe",
  "created_at": "2025-10-25T10:00:00Z"
}
```

---

### PATCH `/api/v1/users/me/password`
Change user password

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password updated successfully"
}
```

---

### DELETE `/api/v1/users/me`
Delete user account

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

---

## Health Check Endpoints

### GET `/api/v1/health/health`
Basic health check

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "PPL Auth Service",
  "version": "1.0.0"
}
```

---

### GET `/api/v1/health/ready`
Readiness check with database connectivity

**Response:** `200 OK`
```json
{
  "status": "ready",
  "service": "PPL Auth Service",
  "version": "1.0.0",
  "database": "connected"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "An error occurred: <error message>"
}
```

---

## Authentication Flow

1. **Register/Login** → Receive `access_token` and `refresh_token`
2. **Use access_token** in `Authorization: Bearer <token>` header for protected endpoints
3. **When access_token expires** → Use `/api/v1/auth/refresh` with `refresh_token`
4. **Logout** → Delete tokens on client side

---

## Token Expiration

- **Access Token**: 30 minutes (configurable)
- **Refresh Token**: 7 days (configurable)

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
