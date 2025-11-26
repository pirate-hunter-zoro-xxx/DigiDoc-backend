"""
Script to create an initial super admin user
Run this script to bootstrap your application with a super admin account

Usage:
    cd backend
    source ../.venv/bin/activate  # Activate virtual environment
    python3 create_super_admin.py
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_super_admin():
    """Create a super admin user"""
    try:
        from core.database import get_supabase_client
        from core.security import get_password_hash
        from models.user import UserRole
        from datetime import datetime
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("\n💡 Make sure you:")
        print("   1. Activate the virtual environment: source ../.venv/bin/activate")
        print("   2. Install dependencies: pip install -r requirements.txt")
        print("   3. Run from backend directory: cd backend && python3 create_super_admin.py")
        return
    
    # Get user input
    print("=" * 60)
    print("CREATE SUPER ADMIN USER")
    print("=" * 60)
    
    name = input("Enter name: ").strip()
    email = input("Enter email: ").strip()
    password = input("Enter password (min 8 chars): ").strip()
    
    if not name or not email or not password:
        print("❌ Error: All fields are required")
        return
    
    if len(password) < 8:
        print("❌ Error: Password must be at least 8 characters")
        return
    
    # Email validation
    if '@' not in email or '.' not in email.split('@')[1]:
        print("❌ Error: Invalid email format")
        return
    
    # Confirm
    print(f"\n📋 Creating super admin:")
    print(f"   Name: {name}")
    print(f"   Email: {email}")
    print(f"   Role: SUPER_ADMIN")
    
    confirm = input("\nProceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    try:
        # Get Supabase client
        print("\n⏳ Connecting to database...")
        supabase = get_supabase_client()
        
        # Check if user already exists
        print("⏳ Checking for existing user...")
        existing_user = supabase.table("users").select("id, email, role").eq("email", email).execute()
        
        if existing_user.data:
            user = existing_user.data[0]
            print(f"\n⚠️  User with email {email} already exists!")
            print(f"   Role: {user.get('role', 'N/A')}")
            
            # Offer to upgrade to super admin if not already
            if user.get('role') != 'super_admin':
                upgrade = input("\nWould you like to upgrade this user to super_admin? (yes/no): ").strip().lower()
                if upgrade in ['yes', 'y']:
                    update_result = supabase.table("users").update({
                        "role": UserRole.SUPER_ADMIN.value,
                        "is_active": True,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("email", email).execute()
                    
                    if update_result.data:
                        print("\n✅ User upgraded to super_admin successfully!")
                        print(f"   Email: {email}")
                        print(f"   Role: super_admin")
                    else:
                        print("❌ Error: Failed to upgrade user")
            else:
                print("ℹ️  User is already a super_admin")
            return
        
        # Hash password
        print("⏳ Hashing password...")
        hashed_password = get_password_hash(password)
        
        # Create super admin user
        print("⏳ Creating super admin user...")
        now = datetime.utcnow().isoformat()
        user_data = {
            "name": name,
            "email": email,
            "password_hash": hashed_password,
            "role": UserRole.SUPER_ADMIN.value,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        result = supabase.table("users").insert(user_data).execute()
        
        if result.data:
            user = result.data[0]
            print("\n" + "=" * 60)
            print("✅ SUPER ADMIN USER CREATED SUCCESSFULLY!")
            print("=" * 60)
            print(f"   ID:     {user['id']}")
            print(f"   Name:   {user['name']}")
            print(f"   Email:  {user['email']}")
            print(f"   Role:   {user['role']}")
            print(f"   Status: {'Active' if user.get('is_active', True) else 'Inactive'}")
            print("=" * 60)
            print("\n🎉 You can now login with these credentials!")
            print(f"\n📝 Login at: http://localhost:3000/login")
            print(f"   Email:    {email}")
            print(f"   Password: {password}")
            print("\n")
        else:
            print("❌ Error: Failed to create user (no data returned)")
            
    except Exception as e:
        print(f"\n❌ Error creating super admin: {str(e)}")
        print("\n💡 Common issues:")
        print("   • Check your .env file has SUPABASE_URL and SUPABASE_KEY")
        print("   • Verify the users table exists in your database")
        print("   • Ensure the role enum type exists (run 001_add_user_roles.sql)")
        print("   • Check your database connection")
        import traceback
        print("\nFull error trace:")
        traceback.print_exc()

if __name__ == "__main__":
    create_super_admin()
