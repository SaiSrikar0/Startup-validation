from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client


def _load_env() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env_file = repo_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)


_load_env()

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("url")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("key")


def get_supabase_client() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase_status() -> dict[str, object]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {
            "available": False,
            "details": "SUPABASE_URL or SUPABASE_KEY is not configured",
        }

    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table("startups").select("startup_id").limit(1).execute()

        if response.error:
            return {
                "available": False,
                "details": str(response.error),
            }

        return {
            "available": True,
            "details": "Connected to Supabase successfully",
        }
    except Exception as exc:
        return {
            "available": False,
            "details": str(exc),
        }
