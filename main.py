"""
main.py - FastAPI application entry point.
Double-entry ledger backend. Truth layer.
"""
import psycopg2
from dotenv import load_dotenv
import os


from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import get_pool, close_pool
from routes import router


import logging

# Basic structured logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ledgerbend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm the connection pool
    logger.info("Application starting up...")
    await get_pool()
    yield
    # Shutdown: close cleanly
    logger.info("Application shutting down...")
    await close_pool()

app = FastAPI(
    title="Universal Double-Entry Ledger",
    description="""
## The Truth Layer

A universal double-entry accounting backend for one person tracking any real-life
financial movement: cash, goods, currencies, parties, promises.

**Core guarantees:**
- Every transaction balances (debits = credits) — enforced at API and DB level
- Entries are immutable once posted — corrections via reversal only
- Every entry carries: account, direction, party, currency, rate, memo, tags
- Query by any dimension: party, tag, account, currency, date, inventory item

**The golden rule:** `GET /reports/verify-balance` — run this any time to
confirm the entire ledger is mathematically sound.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Load environment variables from .env
load_dotenv()

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "Universal Double-Entry Ledger",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "truth_check": "/api/v1/reports/verify-balance",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}



# Load environment variables from .env
load_dotenv()

# The direct connection test below is just for startup diagnostics.
# The actual app uses asyncpg pool from db.py
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

if all([USER, PASSWORD, HOST, PORT, DBNAME]):
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME,
            sslmode="require",
            connect_timeout=5
        )
        logger.info(f"✅ DB Connectivity Check: Successful (Host: {HOST})")
        connection.close()
    except Exception as e:
        logger.warning(f"⚠️ DB Connectivity Check: Failed. (Error: {e})")
        logger.info("   The app will still try to start, but DB calls will likely fail.")
else:
    logger.info("ℹ️ DB Connectivity Check: Skipped (Missing environment variables).")
