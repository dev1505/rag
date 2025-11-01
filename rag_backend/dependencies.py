import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_db: Client = None


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


def database():
    global _db
    _db = create_client(
        SUPABASE_URL,
        SUPABASE_ANON_KEY,
    )
    return _db
