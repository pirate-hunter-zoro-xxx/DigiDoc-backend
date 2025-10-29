-- ============================================
-- Process Flow Application - Database Schema
-- ============================================

-- 1. Requests Table
CREATE TABLE IF NOT EXISTS requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'DRAFT' NOT NULL,
    -- Status values: DRAFT, SUBMITTED, IN_REVIEW, IN_APPROVAL, APPROVED, REJECTED, CANCELLED
    current_stage_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT requests_status_check CHECK (status IN ('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'IN_APPROVAL', 'APPROVED', 'REJECTED', 'CANCELLED'))
);

-- Indexes for requests table
CREATE INDEX idx_requests_creator ON requests(creator_id);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX idx_requests_current_stage ON requests(current_stage_id);

-- 2. Workflow Stages Table
CREATE TABLE IF NOT EXISTS workflow_stages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    stage_type VARCHAR(50) NOT NULL, -- 'RECOMMEND' or 'APPROVE'
    assigned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL, -- Sequence order (1, 2, 3...)
    status VARCHAR(50) DEFAULT 'PENDING' NOT NULL,
    -- Status values: PENDING, IN_PROGRESS, COMPLETED, SKIPPED
    comments TEXT,
    action VARCHAR(50), -- 'RECOMMENDED', 'APPROVED', 'REJECTED', NULL if pending
    action_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT workflow_stages_type_check CHECK (stage_type IN ('RECOMMEND', 'APPROVE')),
    CONSTRAINT workflow_stages_status_check CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED')),
    CONSTRAINT workflow_stages_action_check CHECK (action IN ('RECOMMENDED', 'APPROVED', 'REJECTED') OR action IS NULL),
    CONSTRAINT workflow_stages_order_positive CHECK (order_index > 0),
    UNIQUE(request_id, order_index)
);

-- Indexes for workflow_stages table
CREATE INDEX idx_workflow_request ON workflow_stages(request_id);
CREATE INDEX idx_workflow_assigned_user ON workflow_stages(assigned_user_id);
CREATE INDEX idx_workflow_status ON workflow_stages(status);
CREATE INDEX idx_workflow_stage_type ON workflow_stages(stage_type);
CREATE INDEX idx_workflow_order ON workflow_stages(request_id, order_index);

-- Add foreign key constraint for current_stage_id in requests
ALTER TABLE requests 
ADD CONSTRAINT fk_requests_current_stage 
FOREIGN KEY (current_stage_id) REFERENCES workflow_stages(id) ON DELETE SET NULL;

-- 3. Request Comments Table (for discussion/collaboration)
CREATE TABLE IF NOT EXISTS request_comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for request_comments table
CREATE INDEX idx_comments_request ON request_comments(request_id);
CREATE INDEX idx_comments_user ON request_comments(user_id);
CREATE INDEX idx_comments_created_at ON request_comments(created_at DESC);

-- 4. Request Attachments Table (optional - for file uploads)
CREATE TABLE IF NOT EXISTS request_attachments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size INTEGER, -- Size in bytes
    file_type VARCHAR(100), -- MIME type
    uploaded_by UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for request_attachments table
CREATE INDEX idx_attachments_request ON request_attachments(request_id);
CREATE INDEX idx_attachments_uploader ON request_attachments(uploaded_by);

-- 5. Notifications Table (for tracking notifications)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id UUID REFERENCES requests(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'REQUEST_ASSIGNED', 'REQUEST_COMPLETED', 'REQUEST_REJECTED', etc.
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for notifications table
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

-- ============================================
-- Row Level Security (RLS) Policies
-- ============================================

-- Enable RLS on all tables
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE request_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE request_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Requests Policies
CREATE POLICY "Users can view requests they created or are part of workflow"
ON requests FOR SELECT
USING (
    creator_id = auth.uid() OR
    id IN (
        SELECT request_id FROM workflow_stages WHERE assigned_user_id = auth.uid()
    )
);

CREATE POLICY "Users can create their own requests"
ON requests FOR INSERT
WITH CHECK (creator_id = auth.uid());

CREATE POLICY "Users can update their own draft requests"
ON requests FOR UPDATE
USING (creator_id = auth.uid() AND status = 'DRAFT');

CREATE POLICY "Users can delete their own draft requests"
ON requests FOR DELETE
USING (creator_id = auth.uid() AND status = 'DRAFT');

-- Workflow Stages Policies
CREATE POLICY "Users can view workflow stages for accessible requests"
ON workflow_stages FOR SELECT
USING (
    request_id IN (
        SELECT id FROM requests WHERE 
        creator_id = auth.uid() OR
        id IN (SELECT request_id FROM workflow_stages WHERE assigned_user_id = auth.uid())
    )
);

CREATE POLICY "Request creators can create workflow stages"
ON workflow_stages FOR INSERT
WITH CHECK (
    request_id IN (SELECT id FROM requests WHERE creator_id = auth.uid() AND status = 'DRAFT')
);

CREATE POLICY "Assigned users can update their workflow stages"
ON workflow_stages FOR UPDATE
USING (assigned_user_id = auth.uid());

-- Request Comments Policies
CREATE POLICY "Users can view comments for accessible requests"
ON request_comments FOR SELECT
USING (
    request_id IN (
        SELECT id FROM requests WHERE 
        creator_id = auth.uid() OR
        id IN (SELECT request_id FROM workflow_stages WHERE assigned_user_id = auth.uid())
    )
);

CREATE POLICY "Users can create comments on accessible requests"
ON request_comments FOR INSERT
WITH CHECK (
    user_id = auth.uid() AND
    request_id IN (
        SELECT id FROM requests WHERE 
        creator_id = auth.uid() OR
        id IN (SELECT request_id FROM workflow_stages WHERE assigned_user_id = auth.uid())
    )
);

-- Attachments Policies
CREATE POLICY "Users can view attachments for accessible requests"
ON request_attachments FOR SELECT
USING (
    request_id IN (
        SELECT id FROM requests WHERE 
        creator_id = auth.uid() OR
        id IN (SELECT request_id FROM workflow_stages WHERE assigned_user_id = auth.uid())
    )
);

CREATE POLICY "Users can upload attachments to accessible requests"
ON request_attachments FOR INSERT
WITH CHECK (
    uploaded_by = auth.uid() AND
    request_id IN (
        SELECT id FROM requests WHERE 
        creator_id = auth.uid() OR
        id IN (SELECT request_id FROM workflow_stages WHERE assigned_user_id = auth.uid())
    )
);

-- Notifications Policies
CREATE POLICY "Users can view their own notifications"
ON notifications FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "Users can update their own notifications"
ON notifications FOR UPDATE
USING (user_id = auth.uid());

-- ============================================
-- Functions and Triggers
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for requests table
CREATE TRIGGER update_requests_updated_at
    BEFORE UPDATE ON requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for request_comments table
CREATE TRIGGER update_comments_updated_at
    BEFORE UPDATE ON request_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Note: Uncomment below to insert sample data
-- Make sure to replace user IDs with actual IDs from your users table

/*
-- Sample request
INSERT INTO requests (title, description, creator_id, status)
VALUES (
    'Purchase New Laptop',
    'Need MacBook Pro 16" M3 for development work',
    'YOUR_USER_ID_HERE',
    'DRAFT'
);

-- Sample workflow stages
INSERT INTO workflow_stages (request_id, stage_type, assigned_user_id, order_index, status)
VALUES
    ((SELECT id FROM requests WHERE title = 'Purchase New Laptop'), 'RECOMMEND', 'MANAGER_USER_ID', 1, 'PENDING'),
    ((SELECT id FROM requests WHERE title = 'Purchase New Laptop'), 'RECOMMEND', 'TECH_LEAD_USER_ID', 2, 'PENDING'),
    ((SELECT id FROM requests WHERE title = 'Purchase New Laptop'), 'APPROVE', 'BUDGET_MANAGER_USER_ID', 3, 'PENDING'),
    ((SELECT id FROM requests WHERE title = 'Purchase New Laptop'), 'APPROVE', 'CTO_USER_ID', 4, 'PENDING');
*/

-- ============================================
-- Verification Queries
-- ============================================

-- Check tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('requests', 'workflow_stages', 'request_comments', 'request_attachments', 'notifications');

-- Check indexes
-- SELECT indexname FROM pg_indexes WHERE tablename IN ('requests', 'workflow_stages', 'request_comments', 'request_attachments', 'notifications');

-- Check RLS policies
-- SELECT schemaname, tablename, policyname FROM pg_policies WHERE tablename IN ('requests', 'workflow_stages', 'request_comments', 'request_attachments', 'notifications');
