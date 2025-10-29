# ⚡ Quick Start Guide

Get your authentication service running in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Node.js 20+ (for frontend)
- Supabase account (free tier works)

---

## 🚀 Backend Setup (2 minutes)

### 1. Create Supabase Project

Visit [supabase.com](https://supabase.com) → New Project

**Get these values:**
- Project URL: `Settings → API → Project URL`
- Service Role Key: `Settings → API → service_role key`

### 2. Set Up Database

Copy this SQL and run in Supabase SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own data"
ON users FOR SELECT
USING (auth.uid() = id);
```

### 3. Configure Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=YOUR_SERVICE_ROLE_KEY
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
```

**Edit `.env`** and replace:
- `YOUR_PROJECT_ID` with your actual project ID
- `YOUR_SERVICE_ROLE_KEY` with your service role key

### 4. Start Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running at http://localhost:8000

Test it: http://localhost:8000/docs

---

## 🎨 Frontend Setup (2 minutes)

### 1. Configure Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Update API URL if needed
# Edit app/page.tsx and app/register/page.tsx
# Change fetch URL to: http://localhost:8000
```

### 2. Start Frontend

```bash
npm run dev
```

✅ Frontend running at http://localhost:3000

---

## ✨ Test It Out (1 minute)

### Register New User

1. Go to http://localhost:3000/register
2. Enter:
   - Name: `Test User`
   - Email: `test@example.com`
   - Password: `SecurePass123!`
3. Click "Register"

### Login

1. Go to http://localhost:3000
2. Enter:
   - Email: `test@example.com`
   - Password: `SecurePass123!`
3. Click "Login"

### View Dashboard

You should be redirected to `/dashboard` with user info!

---

## 🔧 Quick Commands Reference

### Backend
```bash
# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/api/v1/health/health
curl http://localhost:8000/docs  # API documentation

# Check database connection
curl http://localhost:8000/api/v1/health/ready
```

### Frontend
```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

---

## 📝 API Endpoints (Quick Reference)

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### User Management (Requires Auth)
- `GET /api/v1/users/me` - Get profile
- `PUT /api/v1/users/me` - Update profile
- `PATCH /api/v1/users/me/password` - Change password
- `DELETE /api/v1/users/me` - Delete account

### Legacy (Backward Compatible)
- `POST /api/register` - Works with existing frontend
- `POST /api/login` - Works with existing frontend

---

## 🔑 Environment Variables

### Backend `.env`
```env
# Required
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=your-service-role-key
JWT_SECRET_KEY=your-secret-key

# Optional (have defaults)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Generate JWT Secret
```bash
openssl rand -hex 32
```

---

## 🎯 Testing with cURL

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "John Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

Save the `access_token` from response.

### Get Profile
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## ⚠️ Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### Database connection errors
- Verify Supabase URL in `.env`
- Check service role key (not anon key!)
- Test connection: `curl http://localhost:8000/api/v1/health/ready`

### Frontend can't connect
- Check backend is running on port 8000
- Verify API URLs in frontend code
- Check CORS settings in `backend/core/config.py`

### Import errors
- Make sure `pydantic-settings` is installed
- Try: `pip install pydantic-settings==2.11.0`

---

## 📚 Next Steps

1. **Read Full Docs**: [README.md](./README.md)
2. **API Reference**: [docs/API.md](./docs/API.md)
3. **Integration Guide**: [docs/INTEGRATION.md](./docs/INTEGRATION.md)
4. **Migration Guide**: [docs/MIGRATION.md](./docs/MIGRATION.md)

---

## 🎉 You're Ready!

Your authentication service is now running. Start building your SaaS app!

### Quick Wins
- ✅ Secure authentication
- ✅ JWT tokens
- ✅ Password hashing
- ✅ Database integration
- ✅ API documentation
- ✅ Modular architecture

### What's Next?
- Add email verification
- Implement password reset
- Add OAuth providers
- Create admin dashboard
- Build your product features!

---

**Need help?** Check the [README](./README.md) or [API docs](./docs/API.md).
