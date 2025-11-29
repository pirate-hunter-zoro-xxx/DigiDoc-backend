-- ============================================
-- MULTI-TENANCY MIGRATION: ADD ORGANIZATIONS
-- ============================================
-- This migration adds organization support to enable multi-tenancy
-- Run this SQL in your Supabase SQL Editor
--
-- Prerequisites:
-- 1. 000_initial_schema.sql has been run
-- 2. 001_add_user_roles.sql has been run
-- ============================================

-- ============================================
-- STEP 1: CREATE ORGANIZATIONS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Indexes for organizations
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON organizations(is_active);
CREATE INDEX IF NOT EXISTS idx_organizations_created_at ON organizations(created_at DESC);

-- Trigger for updated_at
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- STEP 2: ADD ORGANIZATION_ID TO ALL TABLES
-- ============================================

-- Add to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

-- Add to requests table
ALTER TABLE requests ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

-- Add to workflow_stages table
ALTER TABLE workflow_stages ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

-- Add to request_comments table
ALTER TABLE request_comments ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);


-- ============================================
-- STEP 3: CREATE INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_users_organization ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_requests_organization ON requests(organization_id);
CREATE INDEX IF NOT EXISTS idx_workflow_stages_organization ON workflow_stages(organization_id);
CREATE INDEX IF NOT EXISTS idx_comments_organization ON request_comments(organization_id);

-- ============================================
-- STEP 4: UPDATE RLS POLICIES
-- ============================================
-- Pattern: Super admin sees all data, others see only their organization

-- Enable RLS on organizations table
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- ============================================
-- ORGANIZATIONS TABLE POLICIES
-- ============================================

-- Super admins can do everything with organizations
CREATE POLICY "Super admins can manage organizations"
ON organizations FOR ALL
USING ((SELECT role FROM users WHERE id = auth.uid()) = 'super_admin');

-- All users can view their own organization
CREATE POLICY "Users can view their organization"
ON organizations FOR SELECT
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'super_admin'
    OR
    id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- ============================================
-- USERS TABLE POLICIES
-- ============================================

-- Drop old policies
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

-- New policy: Users can view users in their organization
CREATE POLICY "Users can view organization users"
ON users FOR SELECT
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'super_admin'
    OR
    organization_id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
ON users FOR UPDATE
USING (id = auth.uid());

-- ============================================
-- REQUESTS TABLE POLICIES
-- ============================================

-- Users can view requests in their organization
CREATE POLICY "Users can view organization requests"
ON requests FOR SELECT
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'super_admin'
    OR
    organization_id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- Users can insert requests in their organization
CREATE POLICY "Users can insert requests in their org"
ON requests FOR INSERT
WITH CHECK (
    organization_id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- Users can update their own draft requests
CREATE POLICY "Users can update own draft requests"
ON requests FOR UPDATE
USING (
    creator_id = auth.uid() 
    AND status = 'DRAFT'
);

-- Users can delete their own draft requests
CREATE POLICY "Users can delete own draft requests"
ON requests FOR DELETE
USING (
    creator_id = auth.uid() 
    AND status = 'DRAFT'
);

-- ============================================
-- WORKFLOW STAGES TABLE POLICIES
-- ============================================

-- Users can view workflow stages in their organization
CREATE POLICY "Users can view organization workflow stages"
ON workflow_stages FOR SELECT
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'super_admin'
    OR
    organization_id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- System can insert workflow stages (backend)
CREATE POLICY "System can insert workflow stages"
ON workflow_stages FOR INSERT
WITH CHECK (
    organization_id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- Assigned users can update their workflow stages
CREATE POLICY "Assigned users can update their stages"
ON workflow_stages FOR UPDATE
USING (assigned_user_id = auth.uid());

-- ============================================
-- REQUEST COMMENTS TABLE POLICIES
-- ============================================

-- Users can view comments in their organization
CREATE POLICY "Users can view organization comments"
ON request_comments FOR SELECT
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'super_admin'
    OR
    organization_id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- Users can insert comments in their organization
CREATE POLICY "Users can insert comments in their org"
ON request_comments FOR INSERT
WITH CHECK (
    organization_id = (SELECT organization_id FROM users WHERE id = auth.uid())
);

-- Users can update their own comments
CREATE POLICY "Users can update own comments"
ON request_comments FOR UPDATE
USING (user_id = auth.uid());

-- Users can delete their own comments
CREATE POLICY "Users can delete own comments"
ON request_comments FOR DELETE
USING (user_id = auth.uid());



-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify organizations table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'organizations'
) AS organizations_table_exists;

-- Verify organization_id columns added
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name = 'organization_id'
AND table_schema = 'public'
ORDER BY table_name;

-- Verify indexes created
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE indexname LIKE '%organization%'
ORDER BY tablename, indexname;

-- Verify RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE tablename IN ('organizations', 'users', 'requests', 'workflow_stages', 'request_comments')
ORDER BY tablename, policyname;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 003 completed successfully!';
    RAISE NOTICE 'Next step: Run 004_migrate_existing_data.sql';
END $$;
