# PPL Auth Service - Core SaaS Authentication Template

A production-ready, modular authentication and user management service built with FastAPI and Supabase. Designed as a microservice template for SaaS applications.

## 🌟 Features

- ✅ **User Authentication**: Registration, Login, Logout
- ✅ **JWT Tokens**: Access & Refresh token flow
- ✅ **Password Security**: Bcrypt hashing
- ✅ **User Management**: Profile CRUD operations
- ✅ **Database**: Supabase (PostgreSQL) integration
- ✅ **Modular Architecture**: Easy to extend and maintain
- ✅ **API Versioning**: v1 structure ready for future versions
- ✅ **Health Checks**: Service and database monitoring
- ✅ **Documentation**: Swagger UI & ReDoc

## 📁 Project Structure

```
backend/
├── main.py                      # FastAPI app initialization
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (gitignored)
│
├── core/                        # Core functionality
│   ├── config.py               # Settings & configuration
│   ├── security.py             # JWT & password hashing
│   ├── database.py             # Supabase client
│   └── dependencies.py         # Shared dependencies
│
├── api/v1/                      # API version 1
│   ├── router.py               # Main router
│   └── endpoints/
│       ├── auth.py             # Authentication routes
│       ├── users.py            # User management routes
│       └── health.py           # Health check routes
│
├── models/                      # Pydantic models
│   ├── user.py                 # User schemas
│   └── token.py                # Token schemas
│
├── services/                    # Business logic
│   ├── auth_service.py         # Auth operations
│   └── user_service.py         # User operations
│
├── schemas/                     # Database schemas
│   └── users.sql               # Supabase table schema
│
└── docs/                        # Documentation
    ├── API.md                  # API reference
    └── INTEGRATION.md          # Integration guide
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
JWT_SECRET_KEY=your-secret-key  # Generate with: openssl rand -hex 32
```

### 3. Set Up Supabase

1. Create project at [supabase.com](https://supabase.com)
2. Run SQL from `schemas/users.sql` in Supabase SQL Editor
3. Get Project URL and Service Role Key from Settings → API

**Full setup guide**: See [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)

### 4. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Guide**: [docs/API.md](./docs/API.md)

## 🔗 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user

### User Management (Protected)
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update profile
- `PATCH /api/v1/users/me/password` - Change password
- `DELETE /api/v1/users/me` - Delete account

### Health Checks
- `GET /api/v1/health/health` - Service status
- `GET /api/v1/health/ready` - Readiness with DB check

## 🔄 Backward Compatibility

Legacy endpoints still work:
- `POST /api/register` → redirects to `/api/v1/auth/register`
- `POST /api/login` → redirects to `/api/v1/auth/login`

Your existing frontend will continue to work without changes!

## 🏗️ Architecture Benefits

### Modular Design
- **Easy to extend**: Add new features in separate modules
- **Clear separation**: Routes, business logic, and data models separated
- **Testable**: Each component can be tested independently

### Scalability
- **API Versioning**: Support multiple API versions
- **Service-oriented**: Ready for microservices architecture
- **Database agnostic**: Easy to swap Supabase for other databases

### Maintainability
- **Organized structure**: Find code quickly
- **Type safety**: Pydantic models for validation
- **Documentation**: Inline docs and API specs

## 🔐 Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Tokens**: Signed and expiring tokens
- **Refresh Tokens**: Secure token rotation
- **Row Level Security**: Enabled in Supabase
- **CORS**: Configured for specific origins
- **Input Validation**: Pydantic models

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (coming soon)
pytest
```

## 📦 Adding New Features

### Example: Add Email Verification

1. **Create model**: `models/email.py`
2. **Create service**: `services/email_service.py`
3. **Create endpoint**: `api/v1/endpoints/email.py`
4. **Update router**: Import in `api/v1/router.py`

Simple and organized!

## 🔌 Integration with Other Services

See [docs/INTEGRATION.md](./docs/INTEGRATION.md) for:
- How to integrate payment services
- JWT validation in other services
- Microservice architecture patterns
- Docker Compose examples

## 🌍 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_KEY` | Service role key | Required |
| `JWT_SECRET_KEY` | Secret for JWT signing | Required |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | 7 |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |

## 🚢 Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Render / Railway / Fly.io

1. Set environment variables
2. Use start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Deploy!

## 📚 Additional Documentation

- [API Reference](./docs/API.md) - Complete API documentation
- [Integration Guide](./docs/INTEGRATION.md) - How to integrate with other services
- [Supabase Setup](./SUPABASE_SETUP.md) - Detailed Supabase configuration
- [Quick Start](./QUICKSTART.md) - 5-minute setup guide

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database and auth
- **Pydantic** - Data validation
- **python-jose** - JWT implementation
- **passlib** - Password hashing
- **uvicorn** - ASGI server

## 🤝 Contributing

This is a template project. Feel free to:
- Fork and customize
- Add new features
- Improve documentation
- Share improvements

## 📝 License

MIT License - Use freely for your SaaS projects!

## 🆘 Support

1. Check [docs/API.md](./docs/API.md) for API reference
2. See [docs/INTEGRATION.md](./docs/INTEGRATION.md) for integration help
3. Review error logs in terminal
4. Test endpoints at http://localhost:8000/docs

---

**Built with ❤️ for SaaS developers**
