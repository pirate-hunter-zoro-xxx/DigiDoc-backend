-- ============================================
-- RBAC MIGRATION: Add User Roles
-- Version: 001
-- Date: 2025-11-23
-- Description: Add role-based access control to users table
-- ============================================

-- Prerequisites: 000_initial_schema.sql must be run first
-- Run this in your Supabase SQL Editor for STAGING database

BEGIN;

-- ============================================
-- STEP 1: Create role enum type
-- ============================================

CREATE TYPE user_role AS ENUM ('super_admin', 'admin', 'user');

-- ============================================
-- STEP 2: Add new columns to users table
-- ============================================

ALTER TABLE users 
  ADD COLUMN role user_role DEFAULT 'user' NOT NULL,
  ADD COLUMN is_active BOOLEAN DEFAULT true NOT NULL,
  ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN updated_by UUID REFERENCES users(id);

-- ============================================
-- STEP 3: Create indexes for performance
-- ============================================

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_role_active ON users(role, is_active);

-- ============================================
-- STEP 4: Add comments for documentation
-- ============================================

COMMENT ON COLUMN users.role IS 'User role: super_admin, admin, or user';
COMMENT ON COLUMN users.is_active IS 'Whether user account is active';
COMMENT ON COLUMN users.last_login_at IS 'Timestamp of last successful login';
COMMENT ON COLUMN users.updated_by IS 'User ID who last updated this record';

-- ============================================
-- STEP 5: Update RLS policies to respect is_active
-- ============================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

-- Recreate policies with is_active check
CREATE POLICY "Users can view their own data"
    ON users FOR SELECT
    USING (auth.uid() = id AND is_active = true);

CREATE POLICY "Users can update their own data"
    ON users FOR UPDATE
    USING (auth.uid() = id AND is_active = true);

-- ============================================
-- STEP 6: Create admin policies (for admin endpoints)
-- ============================================

-- Note: These policies work with service role key (backend)
-- They allow backend to bypass RLS when using service role

COMMENT ON TABLE users IS 'Users table with RBAC support. Use service role key for admin operations.';

COMMIT;

-- ============================================
-- POST-MIGRATION STEPS (Run these manually)
-- ============================================

-- 1. Create your first super admin user
-- Replace 'your-email@example.com' with your actual email

-- First, register a regular user through your app, then run:
/*
UPDATE users 
SET role = 'super_admin' 
WHERE email = 'your-email@example.com';
*/

-- Verify the update:
/*
SELECT id, email, name, role, is_active, created_at 
FROM users 
WHERE email = 'your-email@example.com';
*/

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check role enum was created
SELECT typname, enumlabel 
FROM pg_type 
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
WHERE typname = 'user_role'
ORDER BY enumsortorder;

-- Expected output:
-- user_role | super_admin
-- user_role | admin
-- user_role | user

-- Check new columns exist
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('role', 'is_active', 'last_login_at', 'updated_by')
ORDER BY column_name;

-- Check indexes were created
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'users' 
  AND indexname LIKE '%role%'
ORDER BY indexname;

-- Count users by role (should all be 'user' initially)
SELECT role, COUNT(*) as count, COUNT(CASE WHEN is_active THEN 1 END) as active_count
FROM users 
GROUP BY role
ORDER BY role;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ RBAC migration completed successfully!';
    RAISE NOTICE '📝 Next steps:';
    RAISE NOTICE '   1. Create your first super admin user (see comments above)';
    RAISE NOTICE '   2. Continue with Phase 2: Backend Models implementation';
    RAISE NOTICE '   3. Update your backend code to use the new role field';
END $$;
