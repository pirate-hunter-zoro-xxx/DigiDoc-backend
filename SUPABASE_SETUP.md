# Supabase Integration Setup Guide

## Step 1: Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in:
   - **Project Name**: PPL Backend
   - **Database Password**: (save this securely)
   - **Region**: Choose closest to you
5. Click "Create new project"
6. Wait for the project to be ready (takes ~2 minutes)

## Step 2: Create the Users Table

1. In your Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click "New Query"
3. Copy and paste the contents of `supabase_schema.sql`
4. Click "Run" or press Ctrl+Enter
5. You should see "Success. No rows returned"

## Step 3: Get Your Supabase Credentials

1. Go to **Project Settings** (gear icon in left sidebar)
2. Click on **API** tab
3. You'll need two things:

   **a) Project URL:**
   ```
   Copy the URL under "Project URL"
   Example: https://abcdefghijklmnop.supabase.co
   ```

   **b) Service Role Key (Secret):**
   ```
   Under "Project API keys" section
   Click to reveal "service_role" key (NOT anon key)
   This key bypasses Row Level Security
   ```

## Step 4: Configure Backend Environment Variables

1. Open the file: `backend/.env`
2. Replace the placeholder values:

```env
SUPABASE_URL=https://your-actual-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-service-role-key
JWT_SECRET_KEY=your-secret-key-change-this-in-production
```

3. Generate a secure JWT secret key:
```bash
# Run this command in terminal:
openssl rand -hex 32

# Copy the output and use it as your JWT_SECRET_KEY
```

## Step 5: Verify the Integration

1. Make sure all dependencies are installed:
```bash
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
```

2. Start the backend server:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Check for errors in the terminal
4. Visit: http://localhost:8000/docs to see the API documentation

## Step 6: Test the Authentication

1. Start your frontend (if not already running):
```bash
cd frontend
bash start-dev.sh
```

2. Go to http://localhost:3000
3. Register a new user
4. Check Supabase dashboard → Table Editor → users table
5. You should see your new user with hashed password!

## Step 7: Verify Data in Supabase

1. In Supabase dashboard, go to **Table Editor**
2. Select **users** table
3. You should see columns:
   - id (UUID)
   - email
   - name
   - password_hash (bcrypt hashed)
   - created_at
   - updated_at

## Security Features Implemented

✅ **Password Hashing**: Uses bcrypt for secure password storage
✅ **JWT Tokens**: Secure token-based authentication
✅ **Environment Variables**: Sensitive data stored in .env
✅ **Row Level Security**: Enabled on Supabase table
✅ **CORS Protection**: Limited to specific origins
✅ **Email Validation**: Using Pydantic EmailStr

## Troubleshooting

### Error: "SUPABASE_URL and SUPABASE_KEY must be set"
- Make sure `.env` file exists in backend directory
- Check that the values are not empty or have placeholder text

### Error: "Failed to create user"
- Verify your service_role key (not anon key)
- Check Supabase project is active
- Verify the users table was created correctly

### Error: "Invalid email or password"
- Make sure the user exists in the database
- Check the password is correct
- Verify password hashing is working

### Error: "relation 'users' does not exist"
- Run the SQL schema from supabase_schema.sql
- Make sure you ran it in the correct project

## Next Steps

- [ ] Add password reset functionality
- [ ] Implement email verification
- [ ] Add user profile updates
- [ ] Create refresh token mechanism
- [ ] Add rate limiting for API endpoints
- [ ] Set up proper CORS for production domain

## Important Notes

⚠️ **Never commit your .env file to Git!**
⚠️ **Use service_role key only on backend, never expose it to frontend**
⚠️ **Change JWT_SECRET_KEY before deploying to production**
⚠️ **Set up proper RLS policies for production use**

## Support

If you encounter any issues:
1. Check the backend terminal for error messages
2. Check browser console for frontend errors
3. Verify Supabase project is active and accessible
4. Make sure all environment variables are set correctly
