# Database Migrations

This directory contains database migration scripts for the PPL-UI application.

## Migration Order

### Initial Setup (For Fresh Database)

1. **000_initial_schema.sql** - Creates all base tables
   - Run this FIRST on empty database
   - Creates: users, requests, workflow_stages, comments, attachments, notifications
   - Sets up RLS policies and triggers

2. **001_add_user_roles.sql** - Adds RBAC support
   - Run this AFTER initial schema
   - Adds: role enum, is_active, last_login_at columns
   - Updates RLS policies

3. **001_rollback_user_roles.sql** - Rollback RBAC (emergency only)
   - Only use if migration 001 fails
   - Removes all RBAC columns and enum

## How to Run Migrations

### Using Supabase Dashboard (Recommended)

1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy and paste the SQL from migration file
5. Click **Run** or press `Ctrl/Cmd + Enter`
6. Check the output for success messages

### Step-by-Step for Fresh Database

```bash
# Step 1: Run initial schema
# Copy contents of: 000_initial_schema.sql
# Paste into Supabase SQL Editor and run

# Step 2: Verify tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

# Step 3: Run RBAC migration
# Copy contents of: 001_add_user_roles.sql
# Paste into Supabase SQL Editor and run

# Step 4: Create first super admin
UPDATE users 
SET role = 'super_admin' 
WHERE email = 'your-email@example.com';

# Step 5: Verify migration
SELECT id, email, role, is_active FROM users;
```

## Current Migrations

| Version | File | Description | Status |
|---------|------|-------------|--------|
| 000 | `000_initial_schema.sql` | Initial database schema | ✅ Ready |
| 001 | `001_add_user_roles.sql` | Add RBAC user roles | ✅ Ready |
| 001R | `001_rollback_user_roles.sql` | Rollback RBAC changes | ✅ Ready |

## Migration Best Practices

1. **Always backup** before running migrations on production
2. **Test on staging** first (you're doing this now! ✅)
3. **Run migrations in order** - don't skip versions
4. **Verify each step** - check the output messages
5. **Keep rollback scripts** ready for emergencies

## Troubleshooting

### Error: "relation already exists"
- Table already created, safe to ignore or use `IF NOT EXISTS`

### Error: "type already exists"
- Enum already created, safe to ignore or use `IF NOT EXISTS`

### Error: "constraint violation"
- Data in table conflicts with migration
- Check existing data before adding constraints

### Error: "permission denied"
- Make sure you're using the correct database credentials
- Use service role key for admin operations

## Creating New Migrations

When adding new migrations:

1. Name format: `00X_description.sql`
2. Include version number in BEGIN comment
3. Use transactions (BEGIN/COMMIT)
4. Add verification queries
5. Create corresponding rollback script
6. Test on local/staging first
7. Update this README

## Post-Migration Tasks

After running RBAC migration (001):

1. Create first super admin user:
```sql
UPDATE users SET role = 'super_admin' WHERE email = 'your-email@example.com';
```

2. Verify role distribution:
```sql
SELECT role, COUNT(*) as count FROM users GROUP BY role;
```

3. Test authentication with new role field

4. Update backend code to use roles

## Support

If you encounter issues:
- Check Supabase logs in Dashboard → Logs
- Verify your database version
- Review RLS policies if access issues occur
- Test with service role key for admin operations
