# Multi-Tenancy Migration Guide

## 📋 Phase 1: Database Migration

This guide walks you through running the database migrations for multi-tenancy support.

---

## ✅ Prerequisites

Before running these migrations:

1. **Backup your database** (always!)
2. Ensure you have access to Supabase SQL Editor
3. Your database should have these tables:
   - `users` (with role column)
   - `requests`
   - `workflow_stages`
   - `request_comments`
   - `request_attachments`
   - `notifications`

---

## 🚀 Migration Steps

### Step 1: Run Migration 003

This migration adds the organizations infrastructure:
- Creates `organizations` table
- Adds `organization_id` column to all relevant tables
- Creates indexes for performance
- Updates RLS (Row Level Security) policies

**How to run:**

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Copy the entire content of `backend/schemas/migrations/003_add_organizations.sql`
4. Paste into SQL Editor
5. Click "Run"

**Expected output:**
```
✅ Migration 003 completed successfully!
Next step: Run 004_migrate_existing_data.sql
```

**Verification:**
The script includes verification queries at the end. Check that:
- `organizations` table exists
- All tables have `organization_id` column
- Indexes are created
- RLS policies are in place

---

### Step 2: Run Migration 004

This migration migrates your existing data:
- Creates a "Default Organization"
- Assigns all existing users (except super admins) to default org
- Assigns all requests, workflow stages, comments, attachments, notifications to appropriate organizations

**How to run:**

1. In Supabase SQL Editor
2. Copy the entire content of `backend/schemas/migrations/004_migrate_existing_data.sql`
3. Paste into SQL Editor
4. Click "Run"

**Expected output:**
```
========================================
✅ MIGRATION COMPLETED SUCCESSFULLY!
========================================
Default Organization ID: <uuid>
Users migrated: X
Requests migrated: X
Workflow stages migrated: X
Comments migrated: X
Attachments migrated: X
Notifications migrated: X
========================================
```

**Verification:**
The script includes verification queries. Check that:
- All non-super-admin users have `organization_id`
- All requests have `organization_id`
- All workflow stages have `organization_id`
- Organization summary shows correct counts

---

## 🧪 Testing the Migration

After running both migrations, test that data isolation works:

### Test 1: Check Default Organization
```sql
SELECT * FROM organizations WHERE slug = 'default-org';
```
Should return 1 organization.

### Test 2: Verify User Assignment
```sql
SELECT 
    role,
    COUNT(*) as total,
    COUNT(organization_id) as with_org,
    COUNT(*) - COUNT(organization_id) as without_org
FROM users
GROUP BY role;
```
- Super admins may have NULL organization_id (expected)
- All other users should have organization_id

### Test 3: Verify Data Isolation
```sql
-- Check that requests inherit organization from creator
SELECT 
    r.id,
    r.title,
    u.email as creator_email,
    r.organization_id = u.organization_id as org_matches
FROM requests r
JOIN users u ON r.creator_id = u.id
WHERE r.organization_id IS NOT NULL
LIMIT 10;
```
All rows should show `org_matches = true`.

### Test 4: Test RLS Policies
Create a test query as a specific user:
```sql
-- This should only show requests from user's organization
SET LOCAL auth.uid = '<some-user-id>';
SELECT * FROM requests;
```

---

## 🔄 Rollback (If Needed)

If something goes wrong, you can rollback the data migration (004):

1. Open the rollback script at the end of `004_migrate_existing_data.sql`
2. Uncomment the DO block
3. Run it in Supabase SQL Editor

**Warning:** This will:
- Set all `organization_id` columns to NULL
- Delete the default organization
- You'll need to re-run migration 004 to restore

---

## ⚠️ Common Issues

### Issue 1: "relation already exists"
**Cause:** Migration 003 was already partially run
**Solution:** Migrations use `IF NOT EXISTS`, so re-running is safe

### Issue 2: "column organization_id does not exist"
**Cause:** Migration 003 didn't complete
**Solution:** Run migration 003 again

### Issue 3: "foreign key constraint violation"
**Cause:** Data references that don't exist
**Solution:** Check your data integrity before migration

### Issue 4: RLS policies blocking queries
**Cause:** Supabase service role needed
**Solution:** Ensure you're using service role key in backend, not anon key

---

## ✅ Success Checklist

After completing Phase 1, verify:

- [ ] `organizations` table exists and has 1 row (default org)
- [ ] All tables have `organization_id` column
- [ ] All indexes created successfully
- [ ] RLS policies are active on all tables
- [ ] All non-super-admin users have `organization_id`
- [ ] All requests have `organization_id`
- [ ] All workflow stages have `organization_id`
- [ ] No errors in Supabase logs
- [ ] Verification queries return expected results

---

## 📝 Next Steps

Once Phase 1 is complete:

1. ✅ Commit the migration files
2. ➡️ Move to Phase 2: Backend Models
3. Update `backend/models/` files with organization_id

---

## 🆘 Need Help?

If you encounter issues:

1. Check Supabase logs for detailed error messages
2. Verify all prerequisites are met
3. Ensure you have proper database permissions
4. Check that previous migrations (000, 001) ran successfully

---

## 📊 Migration File Locations

```
backend/schemas/migrations/
├── 003_add_organizations.sql      (Infrastructure)
└── 004_migrate_existing_data.sql  (Data migration)
```

Both files are now created and ready to run in Supabase!
