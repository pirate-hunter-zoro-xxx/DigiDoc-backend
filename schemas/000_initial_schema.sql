-- ============================================
-- INITIAL DATABASE SCHEMA SETUP
-- Version: 000 (Base Schema)
-- Date: 2025-11-23
-- Description: Complete initial schema for fresh database
-- ============================================

-- Run this FIRST on your empty staging database
-- This creates all existing tables before RBAC migration

BEGIN;

-- ============================================
-- 1. USERS TABLE (Base)
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- 2. REQUESTS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'DRAFT' NOT NULL,
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

-- ============================================
-- 3. WORKFLOW STAGES TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS workflow_stages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    stage_type VARCHAR(50) NOT NULL,
    assigned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING' NOT NULL,
    comments TEXT,
    action VARCHAR(50),
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

-- ============================================
-- 4. REQUEST COMMENTS TABLE
-- ============================================

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

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

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
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE request_comments ENABLE ROW LEVEL SECURITY;

-- Users Policies
CREATE POLICY "Users can view their own data"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own data"
    ON users FOR UPDATE
    USING (auth.uid() = id);

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

COMMIT;

-- ============================================
-- VERIFICATION
-- ============================================

-- Verify tables created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'requests', 'workflow_stages', 'request_comments')
ORDER BY table_name;

-- Should return 4 tables:
-- request_comments, requests, users, workflow_stages

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Initial schema created successfully!';
    RAISE NOTICE 'Next step: Run 001_add_user_roles.sql for RBAC migration';
END $$;
