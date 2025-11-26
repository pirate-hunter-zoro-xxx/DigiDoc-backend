-- ============================================
-- MIGRATION: Add created_by column
-- Version: 002
-- Date: 2025-11-24
-- Description: Add created_by column to users table for audit trail
-- ============================================

-- Prerequisites: 001_add_user_roles.sql must be run first
-- Run this in your Supabase SQL Editor

BEGIN;

-- ============================================
-- Add created_by column
-- ============================================

-- Check if column doesn't exist before adding
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'created_by'
    ) THEN
        ALTER TABLE users 
        ADD COLUMN created_by UUID REFERENCES users(id);
        
        RAISE NOTICE '✅ created_by column added successfully';
    ELSE
        RAISE NOTICE 'ℹ️  created_by column already exists';
    END IF;
END $$;

-- ============================================
-- Add comment for documentation
-- ============================================

COMMENT ON COLUMN users.created_by IS 'User ID who created this user record (for admin-created users)';

-- ============================================
-- Create index for performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_users_created_by ON users(created_by);

COMMIT;

-- ============================================
-- Verification
-- ============================================

-- Check column was added
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'created_by';

-- Expected output:
-- column_name | data_type | is_nullable | column_default
-- created_by  | uuid      | YES         | NULL

-- ============================================
-- SUCCESS MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002 completed successfully!';
    RAISE NOTICE '📝 The created_by column has been added to the users table';
    RAISE NOTICE '   This column will track which admin created each user';
END $$;
