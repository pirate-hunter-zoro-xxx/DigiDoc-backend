-- ============================================
-- MULTI-TENANCY MIGRATION: MIGRATE EXISTING DATA
-- ============================================
-- This migration creates a default organization and assigns
-- all existing data to it
-- Run this AFTER 003_add_organizations.sql
-- ============================================

-- ============================================
-- MIGRATE EXISTING DATA TO DEFAULT ORGANIZATION
-- ============================================

DO $$
DECLARE
    default_org_id UUID;
    affected_users INT;
    affected_requests INT;
    affected_stages INT;
    affected_comments INT;
    affected_attachments INT;
    affected_notifications INT;
BEGIN
    RAISE NOTICE '🚀 Starting data migration to default organization...';
    
    -- ============================================
    -- STEP 1: Create default organization
    -- ============================================
    INSERT INTO organizations (name, slug, description, is_active)
    VALUES (
        'Default Organization',
        'default-org',
        'Auto-created organization for existing data migration',
        true
    )
    RETURNING id INTO default_org_id;
    
    RAISE NOTICE '✅ Created default organization with ID: %', default_org_id;
    
    -- ============================================
    -- STEP 2: Assign non-super-admin users to default org
    -- ============================================
    UPDATE users 
    SET organization_id = default_org_id
    WHERE role != 'super_admin' 
    AND organization_id IS NULL;
    
    GET DIAGNOSTICS affected_users = ROW_COUNT;
    RAISE NOTICE '✅ Assigned % users to default organization', affected_users;
    
    -- ============================================
    -- STEP 3: Assign requests based on creator's organization
    -- ============================================
    UPDATE requests 
    SET organization_id = u.organization_id
    FROM users u
    WHERE requests.creator_id = u.id 
    AND requests.organization_id IS NULL
    AND u.organization_id IS NOT NULL;
    
    GET DIAGNOSTICS affected_requests = ROW_COUNT;
    RAISE NOTICE '✅ Assigned % requests to organizations', affected_requests;
    
    -- ============================================
    -- STEP 4: Assign workflow stages from their requests
    -- ============================================
    UPDATE workflow_stages 
    SET organization_id = r.organization_id
    FROM requests r
    WHERE workflow_stages.request_id = r.id 
    AND workflow_stages.organization_id IS NULL
    AND r.organization_id IS NOT NULL;
    
    GET DIAGNOSTICS affected_stages = ROW_COUNT;
    RAISE NOTICE '✅ Assigned % workflow stages to organizations', affected_stages;
    
    -- ============================================
    -- STEP 5: Assign comments from their requests
    -- ============================================
    UPDATE request_comments 
    SET organization_id = r.organization_id
    FROM requests r
    WHERE request_comments.request_id = r.id 
    AND request_comments.organization_id IS NULL
    AND r.organization_id IS NOT NULL;
    
    GET DIAGNOSTICS affected_comments = ROW_COUNT;
    RAISE NOTICE '✅ Assigned % comments to organizations', affected_comments;
    

    
    -- ============================================
    -- STEP 8: Summary
    -- ============================================
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ MIGRATION COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Default Organization ID: %', default_org_id;
    RAISE NOTICE 'Users migrated: %', affected_users;
    RAISE NOTICE 'Requests migrated: %', affected_requests;
    RAISE NOTICE 'Workflow stages migrated: %', affected_stages;
    RAISE NOTICE 'Comments migrated: %', affected_comments;
    RAISE NOTICE '========================================';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '❌ Migration failed: %', SQLERRM;
        ROLLBACK;
END $$;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify all non-super-admin users have organization_id
SELECT 
    COUNT(*) AS users_without_org,
    ARRAY_AGG(email) AS affected_emails
FROM users 
WHERE organization_id IS NULL 
AND role != 'super_admin';

-- Verify all requests have organization_id
SELECT 
    COUNT(*) AS requests_without_org
FROM requests 
WHERE organization_id IS NULL;

-- Verify workflow stages have organization_id
SELECT 
    COUNT(*) AS stages_without_org
FROM workflow_stages 
WHERE organization_id IS NULL;

-- Show organization summary
SELECT 
    o.name AS organization_name,
    o.slug,
    COUNT(DISTINCT u.id) AS user_count,
    COUNT(DISTINCT r.id) AS request_count,
    COUNT(DISTINCT ws.id) AS workflow_stage_count
FROM organizations o
LEFT JOIN users u ON o.id = u.organization_id
LEFT JOIN requests r ON o.id = r.organization_id
LEFT JOIN workflow_stages ws ON o.id = ws.organization_id
GROUP BY o.id, o.name, o.slug
ORDER BY o.created_at;

-- ============================================
-- ROLLBACK SCRIPT (IF NEEDED)
-- ============================================
-- WARNING: Only use this if you need to undo the migration
-- Uncomment the following to rollback:

/*
DO $$
BEGIN
    -- Remove organization_id from all tables
    UPDATE users SET organization_id = NULL;
    UPDATE requests SET organization_id = NULL;
    UPDATE workflow_stages SET organization_id = NULL;
    UPDATE request_comments SET organization_id = NULL;
    UPDATE request_attachments SET organization_id = NULL;
    UPDATE notifications SET organization_id = NULL;
    
    -- Delete default organization
    DELETE FROM organizations WHERE slug = 'default-org';
    
    RAISE NOTICE 'Migration rolled back successfully';
END $$;
*/
