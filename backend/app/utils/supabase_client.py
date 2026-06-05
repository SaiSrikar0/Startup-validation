from supabase import create_client, Client

from .config import SUPABASE_URL, SUPABASE_KEY


try:
    supabase: Client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )
except Exception as e:
    raise RuntimeError(
        f"Failed to initialize Supabase client: {e}"
    )


def get_supabase() -> Client:
    """
    Returns the initialized Supabase client.
    """
    return supabase