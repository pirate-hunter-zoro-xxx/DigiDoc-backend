# Process Flow Application - Setup Guide

## 🚀 Quick Setup

### 1. Run Database Schema

Go to your Supabase Dashboard:
1. Open **SQL Editor**
2. Copy the entire content from `backend/schemas/requests.sql`
3. Click **Run** to create all tables

This will create:
- ✅ `requests` table
- ✅ `workflow_stages` table
- ✅ `request_comments` table
- ✅ `request_attachments` table
- ✅ `notifications` table
- ✅ All indexes and RLS policies
- ✅ Triggers for auto-updating timestamps

### 2. Start Backend

```bash
cd backend
source .venv/bin/activate  # Or: .venv\Scripts\activate on Windows
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test API

Visit http://localhost:8000/docs

You'll see new endpoint sections:
- **Requests** - 8 endpoints for request management
- **Workflow** - 5 endpoints for workflow actions

## 📖 API Endpoints

### Requests API (`/api/v1/requests`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/requests` | Create new request |
| GET | `/api/v1/requests` | List user's requests |
| GET | `/api/v1/requests/{id}` | Get request details |
| PUT | `/api/v1/requests/{id}` | Update request (DRAFT only) |
| DELETE | `/api/v1/requests/{id}` | Delete request (DRAFT only) |
| POST | `/api/v1/requests/{id}/comments` | Add comment |
| GET | `/api/v1/requests/{id}/comments` | Get comments |

### Workflow API (`/api/v1/workflow`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflow/requests/{id}/submit` | Submit request for review |
| POST | `/api/v1/workflow/requests/{id}/cancel` | Cancel request |
| GET | `/api/v1/workflow/pending` | Get pending actions |
| POST | `/api/v1/workflow/stages/{id}/action` | Take action (recommend/approve/reject) |
| GET | `/api/v1/workflow/requests/{id}/history` | Get workflow history |

## 🧪 Testing the Workflow

### Step 1: Create a Request (as User A)

```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Purchase New Laptop",
    "description": "Need MacBook Pro 16\" M3 for development",
    "workflow_stages": [
      {
        "stage_type": "RECOMMEND",
        "assigned_user_id": "USER_B_ID",
        "order_index": 1
      },
      {
        "stage_type": "APPROVE",
        "assigned_user_id": "USER_C_ID",
        "order_index": 2
      }
    ]
  }'
```

### Step 2: Submit Request (as User A)

```bash
curl -X POST http://localhost:8000/api/v1/workflow/requests/{REQUEST_ID}/submit \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 3: Check Pending Actions (as User B)

```bash
curl -X GET http://localhost:8000/api/v1/workflow/pending \
  -H "Authorization: Bearer USER_B_TOKEN"
```

### Step 4: Recommend (as User B)

```bash
curl -X POST http://localhost:8000/api/v1/workflow/stages/{STAGE_ID}/action \
  -H "Authorization: Bearer USER_B_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "RECOMMENDED",
    "comments": "Looks good from technical perspective"
  }'
```

### Step 5: Approve (as User C)

```bash
curl -X POST http://localhost:8000/api/v1/workflow/stages/{STAGE_ID}/action \
  -H "Authorization: Bearer USER_C_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "APPROVED",
    "comments": "Budget approved"
  }'
```

## 📊 Request Status Flow

```
DRAFT → SUBMITTED → IN_REVIEW → IN_APPROVAL → APPROVED
                                              ↓
                                           REJECTED
```

## 🎯 Next Steps

1. ✅ Backend API is ready
2. ⏭️ Build Frontend UI
3. ⏭️ Add Notification System
4. ⏭️ Test End-to-End

## 🔧 Troubleshooting

### Import Errors
If you get import errors, make sure you're in the backend directory:
```bash
cd backend
python -c "from models.request import RequestCreate"
```

### Database Errors
Check if tables were created:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('requests', 'workflow_stages');
```

### Token Issues
Make sure you're using a valid JWT token from login:
```bash
# Login first
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use the access_token from response
```

## 📝 What's Built

### Backend ✅
- Database schema with 5 tables
- Pydantic models with 15+ schemas
- Request service with CRUD operations
- Workflow service with sequential logic
- 13 API endpoints
- RLS policies for security
- Auto-updating timestamps

### Frontend ⏳
- Next phase: Build React components
- Pages needed: List, Create, Detail, Workflow Dashboard

---

**Ready to build the frontend?** Let me know! 🚀
