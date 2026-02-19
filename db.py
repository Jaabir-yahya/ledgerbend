"""
db.py - Supabase / PostgreSQL connection
Uses asyncpg for async queries. One pool, shared across the app.
"""
import os
import asyncpg
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Fetch individual variables from .env as the user has them now
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "6543")
DB_NAME = os.getenv("dbname")

# Construct DATABASE_URL if all variables are present, else fallback
if all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/ledger"
    )

# Supabase direct connection (use the "direct" connection string, not pooler,
# for DDL and functions. Switch to pooler for high-traffic reads if needed.)
# Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        print(f"DEBUG: Connecting to {DATABASE_URL.split('@')[-1]}")
        try:
            _pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60,
                ssl="require",
                statement_cache_size=0
            )
        except Exception as e:
            print(f"DEBUG: Connection failed: {e}")
            raise
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_conn():
    """Get a connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def get_db() -> AsyncGenerator:
    """FastAPI dependency: yields a connection."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
