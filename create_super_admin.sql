-- ============================================
-- CREATE SUPER ADMIN USER
-- ============================================
-- Run this SQL directly in your Supabase SQL Editor
-- 
-- Prerequisites:
-- 1. 000_initial_schema.sql has been run
-- 2. 001_add_user_roles.sql has been run
-- ============================================

-- ============================================
-- METHOD 1: Insert with pre-generated hash
-- ============================================

-- Password: Admin@123456
-- Hash generated: $2b$12$ZBgynLK79VKduyhSltfcBew6P9bgTg5AoEzhCuPI5KxqjpF9AGkxi

INSERT INTO users (
    name,
    email,
    password_hash,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Super Admin',
    'admin@digidoc.com',
    '$2b$12$ZBgynLK79VKduyhSltfcBew6P9bgTg5AoEzhCuPI5KxqjpF9AGkxi',
    'super_admin',
    true,
    NOW(),
    NOW()
)
RETURNING id, name, email, role, is_active, created_at;

-- ============================================
-- Verify the insert
-- ============================================

SELECT id, name, email, role, is_active, created_at
FROM users
WHERE email = 'admin@digidoc.com';

-- ============================================
-- Login Credentials
-- ============================================
-- Email:    admin@digidoc.com
-- Password: Admin@123456
--
-- Login URL: http://localhost:3000/login
-- ============================================

-- ============================================
-- METHOD 2: Create your own super admin
-- ============================================

-- Step 1: Generate a password hash
-- Go to: https://bcrypt-generator.com/
-- Enter your password
-- Use "Rounds: 12"
-- Copy the generated hash

-- Step 2: Replace the values below and run

/*
INSERT INTO users (
    name,
    email,
    password_hash,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Your Name',                    -- Change this
    'your.email@example.com',       -- Change this
    '$2b$12$YOUR_GENERATED_HASH',   -- Change this
    'super_admin',
    true,
    NOW(),
    NOW()
);
*/

-- ============================================
-- METHOD 3: Upgrade existing user
-- ============================================

-- If you already have a user account, upgrade it to super_admin:

/*
UPDATE users 
SET 
    role = 'super_admin',
    is_active = true,
    updated_at = NOW()
WHERE email = 'your.email@example.com';
*/

-- Verify the upgrade:
/*
SELECT id, name, email, role, is_active
FROM users
WHERE email = 'your.email@example.com';
*/

-- ============================================
-- Additional Admin Users (Run after super admin is created)
-- ============================================

-- Create a regular admin user (for testing)
-- Password: Admin@123

/*
INSERT INTO users (
    name,
    email,
    password_hash,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Admin User',
    'admin.user@digidoc.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPwbR2oYqy',
    'admin',
    true,
    NOW(),
    NOW()
);
*/

-- Create a regular user (for testing)
-- Password: User@123

/*
INSERT INTO users (
    name,
    email,
    password_hash,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Regular User',
    'user@digidoc.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPwbR2oYqy',
    'user',
    true,
    NOW(),
    NOW()
);
*/

-- ============================================
-- Verify All Users
-- ============================================

SELECT 
    id,
    name,
    email,
    role,
    is_active,
    created_at,
    last_login_at
FROM users
ORDER BY 
    CASE role
        WHEN 'super_admin' THEN 1
        WHEN 'admin' THEN 2
        WHEN 'user' THEN 3
    END,
    created_at DESC;

-- ============================================
-- User Statistics
-- ============================================

SELECT 
    role,
    COUNT(*) as total,
    COUNT(CASE WHEN is_active THEN 1 END) as active,
    COUNT(CASE WHEN NOT is_active THEN 1 END) as inactive
FROM users
GROUP BY role
ORDER BY 
    CASE role
        WHEN 'super_admin' THEN 1
        WHEN 'admin' THEN 2
        WHEN 'user' THEN 3
    END;

-- ============================================
-- SUCCESS!
-- ============================================
-- You can now:
-- 1. Start your backend: cd backend && uvicorn main:app --reload
-- 2. Start your frontend: cd frontend && npm run dev
-- 3. Login at: http://localhost:3000/login
-- ============================================
