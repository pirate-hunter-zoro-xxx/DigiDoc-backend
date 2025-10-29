# Process Flow Application - Implementation Plan

## 🎯 Overview

A workflow management system where users can:
- Create requests with title, description, and attachments
- Add recommenders (sequential review/feedback)
- Add approvers (sequential approval)
- Track request status through workflow stages
- Receive notifications at each stage

---

## 📊 System Architecture

### Workflow Flow
```
Creator → Submit Request
    ↓
Recommender 1 → Review & Recommend
    ↓
Recommender 2 → Review & Recommend (if multiple)
    ↓
Approver 1 → Approve/Reject
    ↓
Approver 2 → Approve/Reject (if multiple)
    ↓
Final Status: APPROVED or REJECTED
```

---

## 🗄️ Database Schema

### 1. `requests` Table
```sql
CREATE TABLE requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'DRAFT',
    -- Status: DRAFT, SUBMITTED, IN_REVIEW, IN_APPROVAL, APPROVED, REJECTED, CANCELLED
    current_stage_id UUID REFERENCES workflow_stages(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_requests_creator ON requests(creator_id);
CREATE INDEX idx_requests_status ON requests(status);
```

### 2. `workflow_stages` Table
```sql
CREATE TABLE workflow_stages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    stage_type VARCHAR(50) NOT NULL, -- 'RECOMMEND' or 'APPROVE'
    assigned_user_id UUID NOT NULL REFERENCES users(id),
    order_index INTEGER NOT NULL, -- Sequence order (1, 2, 3...)
    status VARCHAR(50) DEFAULT 'PENDING',
    -- Status: PENDING, IN_PROGRESS, COMPLETED, SKIPPED
    comments TEXT,
    action VARCHAR(50), -- 'RECOMMENDED', 'APPROVED', 'REJECTED'
    action_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(request_id, order_index)
);

CREATE INDEX idx_workflow_request ON workflow_stages(request_id);
CREATE INDEX idx_workflow_user ON workflow_stages(assigned_user_id);
CREATE INDEX idx_workflow_status ON workflow_stages(status);
```

### 3. `request_attachments` Table (Optional)
```sql
CREATE TABLE request_attachments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size INTEGER,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. `request_comments` Table (Optional - for discussion)
```sql
CREATE TABLE request_comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 📦 Backend Structure

### Models (`backend/models/`)

#### `request.py`
```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RequestStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    IN_APPROVAL = "IN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class StageType(str, Enum):
    RECOMMEND = "RECOMMEND"
    APPROVE = "APPROVE"

class StageStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"

class StageAction(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

# Request Models
class WorkflowStageCreate(BaseModel):
    stage_type: StageType
    assigned_user_id: str
    order_index: int

class RequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    workflow_stages: List[WorkflowStageCreate] = []

class RequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class RequestResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    creator_id: str
    creator_name: str
    status: RequestStatus
    current_stage_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]

class RequestDetailResponse(RequestResponse):
    workflow_stages: List["WorkflowStageResponse"]

# Workflow Stage Models
class WorkflowStageResponse(BaseModel):
    id: str
    request_id: str
    stage_type: StageType
    assigned_user_id: str
    assigned_user_name: str
    order_index: int
    status: StageStatus
    comments: Optional[str]
    action: Optional[StageAction]
    action_at: Optional[datetime]
    created_at: datetime

class StageActionRequest(BaseModel):
    action: StageAction
    comments: Optional[str] = None
```

### Services (`backend/services/`)

#### `request_service.py`
```python
Key Functions:
- create_request(creator_id, request_data)
- get_request_by_id(request_id)
- list_user_requests(user_id, filter_by_status=None)
- update_request(request_id, updates)
- delete_request(request_id)
- add_workflow_stages(request_id, stages)
- submit_request(request_id) # Changes status from DRAFT to SUBMITTED
```

#### `workflow_service.py`
```python
Key Functions:
- get_current_stage(request_id)
- get_pending_actions(user_id) # Requests where user is next in workflow
- take_action(stage_id, user_id, action, comments)
- advance_workflow(request_id) # Move to next stage
- complete_workflow(request_id, final_status)
- get_workflow_history(request_id)
- validate_stage_order(request_id, stage_id) # Ensure sequential processing
```

### API Endpoints (`backend/api/v1/endpoints/`)

#### `requests.py`
```python
POST   /api/v1/requests                    # Create request (DRAFT)
GET    /api/v1/requests                    # List user's requests
GET    /api/v1/requests/{id}               # Get request details + workflow
PUT    /api/v1/requests/{id}               # Update request (only if DRAFT)
DELETE /api/v1/requests/{id}               # Delete request (only if DRAFT)
POST   /api/v1/requests/{id}/submit        # Submit for review
POST   /api/v1/requests/{id}/cancel        # Cancel request
GET    /api/v1/requests/{id}/workflow      # Get workflow stages
```

#### `workflow.py`
```python
GET    /api/v1/workflow/pending            # My pending actions
GET    /api/v1/workflow/completed          # My completed actions
POST   /api/v1/workflow/stages/{id}/action # Take action (recommend/approve/reject)
GET    /api/v1/workflow/requests/{id}/history # Full workflow history
```

---

## 🎨 Frontend Structure

### Pages

#### 1. **Requests Dashboard** (`app/requests/page.tsx`)
```
Features:
- List all user's requests with filters (status, date)
- Tabs: My Requests | Pending Actions | Completed
- Quick actions: View, Edit (if DRAFT), Cancel
- Status badges with colors
- Search and filter
```

#### 2. **Create Request** (`app/requests/create/page.tsx`)
```
Features:
- Form: Title, Description
- Add Recommenders section (search users, set order)
- Add Approvers section (search users, set order)
- Preview workflow sequence
- Save as Draft or Submit directly
- Drag-and-drop to reorder workflow
```

#### 3. **Request Details** (`app/requests/[id]/page.tsx`)
```
Features:
- Request information (title, description, creator, dates)
- Workflow timeline/stepper component
  - Shows all stages with status
  - Highlight current stage
  - Show completed stages with user, action, timestamp
- Comments/feedback from each stage
- Edit button (if DRAFT and user is creator)
- Action buttons (if user is assigned to current stage)
```

#### 4. **Workflow Action** (`app/workflow/page.tsx`)
```
Features:
- Dashboard showing all pending actions
- Card view: Request title, creator, submitted date, stage type
- Quick action buttons: Recommend, Approve, Reject
- Action modal: Add comments, confirm action
- Filter: Recommendations | Approvals
```

---

## 🔄 Workflow Logic

### Sequential Processing Rules

1. **Stage Validation**
   - Users can only act on their assigned stage
   - Can only act when previous stages are completed
   - Cannot skip stages

2. **Status Transitions**
   ```
   DRAFT → SUBMITTED (when user clicks submit)
   SUBMITTED → IN_REVIEW (when first recommender starts)
   IN_REVIEW → IN_APPROVAL (when all recommendations done)
   IN_APPROVAL → APPROVED (when all approvals done)
   IN_APPROVAL → REJECTED (if any approver rejects)
   ANY → CANCELLED (creator can cancel)
   ```

3. **Stage Status Transitions**
   ```
   PENDING → IN_PROGRESS (when user opens action)
   IN_PROGRESS → COMPLETED (when action submitted)
   ```

4. **Auto-Advancement**
   - After stage completion, automatically set next stage to IN_PROGRESS
   - Notify next user via email/notification

---

## 🔔 Notification System

### Notification Triggers

1. **Request Submitted** → Notify first recommender
2. **Stage Completed** → Notify next person in sequence
3. **Request Approved** → Notify creator
4. **Request Rejected** → Notify creator
5. **Request Cancelled** → Notify all participants

### Implementation
```python
# services/notification_service.py

def notify_stage_assigned(user_id, request_id, stage_type):
    # Send email + in-app notification
    pass

def notify_request_completed(creator_id, request_id, final_status):
    # Notify creator of final outcome
    pass
```

---

## 🎯 User Roles & Permissions

### Role: Request Creator
- Create requests
- Add workflow participants
- Submit requests
- Cancel own requests
- View request status

### Role: Recommender
- View assigned requests
- Add recommendations
- Add comments
- Cannot approve/reject

### Role: Approver
- View request + all recommendations
- Approve or reject
- Add comments
- Final decision maker

---

## 🚀 Implementation Phases

### Phase 1: Core Request System (Week 1)
- ✅ Database schema
- ✅ Request models
- ✅ Request CRUD service
- ✅ Request API endpoints
- ✅ Basic frontend: Create & List requests

### Phase 2: Workflow Engine (Week 2)
- ✅ Workflow models
- ✅ Workflow service with sequential logic
- ✅ Workflow API endpoints
- ✅ Frontend: Request details with workflow timeline
- ✅ Frontend: Action page for recommenders/approvers

### Phase 3: Advanced Features (Week 3)
- ✅ Notification system
- ✅ Email notifications
- ✅ Request comments/discussion
- ✅ File attachments
- ✅ Workflow templates

### Phase 4: Enhancements (Week 4)
- ✅ Dashboard with analytics
- ✅ Search and filters
- ✅ Export reports
- ✅ Audit logs
- ✅ Mobile responsive design

---

## 📊 Example User Journey

### Scenario: Employee requests equipment purchase

1. **John (Creator)** creates request:
   - Title: "New Laptop for Development"
   - Description: "MacBook Pro 16" M3 for React development"
   - Adds recommenders: [Manager Sarah (1), Tech Lead Mike (2)]
   - Adds approvers: [Budget Manager Lisa (1), CTO David (2)]
   - Clicks "Submit"

2. **Sarah (Manager)** receives notification:
   - Opens request
   - Reviews details
   - Adds comment: "Approved from team perspective. Essential for performance."
   - Clicks "Recommend"

3. **Mike (Tech Lead)** receives notification:
   - Sees Sarah's recommendation
   - Adds comment: "Specs look good. Current laptop is 4 years old."
   - Clicks "Recommend"

4. **Lisa (Budget Manager)** receives notification:
   - Reviews request + recommendations
   - Checks budget availability
   - Adds comment: "Budget approved. $2500 allocated from Q4."
   - Clicks "Approve"

5. **David (CTO)** receives notification:
   - Final review
   - Sees all previous approvals
   - Clicks "Approve"

6. **John (Creator)** receives notification:
   - "Your request has been approved!"
   - Can proceed with purchase

---

## 🔒 Security Considerations

1. **Authorization**
   - Users can only view requests they created or are part of workflow
   - Stage actions only by assigned users
   - Edit/delete only for DRAFT status by creator

2. **Validation**
   - Prevent duplicate stages
   - Validate sequential order
   - Check user exists before assigning

3. **Audit Trail**
   - Log all actions with timestamps
   - Track who did what and when
   - Immutable workflow history

---

## 📈 Future Enhancements

1. **Parallel Workflows**
   - Multiple approvers can approve simultaneously
   - Require N out of M approvals

2. **Conditional Workflows**
   - If amount > $5000, add extra approver
   - Different workflows based on request type

3. **Workflow Templates**
   - Pre-defined workflows for common scenarios
   - One-click workflow setup

4. **Delegation**
   - Users can delegate their approval to others
   - Temporary out-of-office delegation

5. **Analytics Dashboard**
   - Average approval time
   - Bottleneck identification
   - Approval rates by user

6. **Integration**
   - Slack/Teams notifications
   - Calendar integration
   - Document management system integration

---

## 🛠️ Tech Stack

### Backend
- FastAPI (existing)
- Supabase PostgreSQL (existing)
- JWT Authentication (existing)
- Email service (SendGrid/AWS SES)

### Frontend
- Next.js 15 (existing)
- TypeScript (existing)
- Tailwind CSS (existing)
- React Hook Form (for forms)
- React Query (for API calls)
- Zustand/Context (for state management)

### Additional Libraries
- **Backend**: python-multipart (file uploads), jinja2 (email templates)
- **Frontend**: react-beautiful-dnd (drag-drop), date-fns (date formatting), recharts (analytics)

---

## 📝 Next Steps

1. Review and approve this plan
2. Start with Phase 1: Core Request System
3. Set up database tables in Supabase
4. Implement backend models and services
5. Create API endpoints
6. Build frontend components
7. Test workflow logic thoroughly
8. Deploy and iterate

---

**Total Estimated Time**: 3-4 weeks for full implementation
**Start with**: Database schema → Backend models → API endpoints → Frontend UI

Ready to begin implementation? 🚀
