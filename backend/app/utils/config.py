from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate configuration
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is not set in the .env file")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is not set in the .env file")