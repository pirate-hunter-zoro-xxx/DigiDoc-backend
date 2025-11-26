-- ============================================
-- ROLLBACK: Remove RBAC from Users
-- Version: 001 Rollback
-- Date: 2025-11-23
-- Description: Rollback the RBAC migration
-- ============================================

-- ⚠️ WARNING: This will remove all role assignments!
-- ⚠️ Make sure to backup before running this rollback

BEGIN;

-- ============================================
-- STEP 1: Restore original RLS policies
-- ============================================

-- Drop RBAC-enhanced policies
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

-- Recreate original policies (without is_active check)
CREATE POLICY "Users can view their own data"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own data"
    ON users FOR UPDATE
    USING (auth.uid() = id);

-- ============================================
-- STEP 2: Drop indexes
-- ============================================

DROP INDEX IF EXISTS idx_users_role_active;
DROP INDEX IF EXISTS idx_users_active;
DROP INDEX IF EXISTS idx_users_role;

-- ============================================
-- STEP 3: Drop columns (THIS WILL LOSE DATA!)
-- ============================================

ALTER TABLE users 
  DROP COLUMN IF EXISTS updated_by,
  DROP COLUMN IF EXISTS last_login_at,
  DROP COLUMN IF EXISTS is_active,
  DROP COLUMN IF EXISTS role;

-- ============================================
-- STEP 4: Drop enum type
-- ============================================

DROP TYPE IF EXISTS user_role;

-- ============================================
-- STEP 5: Remove comments
-- ============================================

COMMENT ON TABLE users IS NULL;

COMMIT;

-- ============================================
-- VERIFICATION
-- ============================================

-- Verify columns were removed
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Should NOT see: role, is_active, last_login_at, updated_by

-- Verify enum type was removed
SELECT typname 
FROM pg_type 
WHERE typname = 'user_role';

-- Should return no rows

-- ============================================
-- WARNING MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '⚠️  RBAC rollback completed';
    RAISE NOTICE '❌ All role assignments have been lost';
    RAISE NOTICE '📝 Database restored to pre-RBAC state';
END $$;
