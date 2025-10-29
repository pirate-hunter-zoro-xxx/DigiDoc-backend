from supabase import create_client, Client
from core.config import settings

# Supabase client instance
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance (singleton pattern)
    
    Returns:
        Supabase client instance
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY are not set
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env file. "
                "Please check your configuration."
            )
        
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    return _supabase_client


def test_database_connection() -> bool:
    """
    Test the database connection
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        # Try a simple query to test connection
        result = supabase.table("users").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Database connection test failed: {str(e)}")
        return False
