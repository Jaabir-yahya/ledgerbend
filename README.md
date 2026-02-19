# Universal Double-Entry Ledger
## Phase 1 – The Truth Layer

**Stack:** Supabase (PostgreSQL) + Python + FastAPI  
**Philosophy:** Log any mess accurately now. Unlock infinite possibilities later.

---

## Setup

### 1. Supabase
1. Create a new Supabase project at supabase.com
2. Go to **SQL Editor** and run `schema.sql` in full
3. Copy your **direct connection string** (Settings → Database → Connection String → URI)
   - Use the **direct** connection, not the pooler, for Phase 1

### 2. Environment
```bash
cp .env.example .env
# Edit .env with your DATABASE_URL
```

`.env`:
```
DATABASE_URL=postgresql://postgres.[ref]:[password]@db.[ref].supabase.co:5432/postgres
```

### 3. Install & Run
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs  
Truth check: http://localhost:8000/api/v1/reports/verify-balance

### 4. Run Tests (no DB needed)
```bash
pytest tests/test_truth.py -v
```

---

## File Structure

```
schema.sql          ← Run once in Supabase SQL editor
main.py             ← FastAPI app entry point
db.py               ← Supabase connection pool
models.py           ← Pydantic models (truth in Python)
routes.py           ← All API endpoints
requirements.txt    ← Dependencies
tests/
  test_truth.py     ← Truth verification tests (no DB needed)
```

---

## Key Endpoints

| Method | Path | What it does |
|--------|------|--------------|
| POST | `/api/v1/transactions` | Create + post a balanced transaction |
| GET  | `/api/v1/transactions` | List transactions |
| POST | `/api/v1/transactions/{id}/reverse` | Reverse a posted transaction |
| GET  | `/api/v1/ledger` | Browse entries by any dimension |
| GET  | `/api/v1/reports/trial-balance` | Full trial balance |
| GET  | `/api/v1/reports/party-balances` | Who owes what |
| GET  | `/api/v1/reports/currency-exposure` | Forex positions |
| GET  | `/api/v1/reports/verify-balance` | **The truth check** |
| POST | `/api/v1/accounts` | Create account |
| POST | `/api/v1/parties` | Create party |
| POST | `/api/v1/inventory` | Create inventory item |

---

## How to Record a Transaction

Every real-world event is just entries + context:

```json
POST /api/v1/transactions
{
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "date": "2024-01-15",
  "description": "Import 100 phones from Shenzhen",
  "entries": [
    {
      "account_id": "<inventory-account-id>",
      "debit_amount": 650000,
      "currency_code": "KES",
      "exchange_rate": 1,
      "inventory_item_id": "<phones-item-id>",
      "quantity": 100,
      "tags": ["china-import", "phones"]
    },
    {
      "account_id": "<bank-usd-account-id>",
      "credit_amount": 5000,
      "currency_code": "USD",
      "exchange_rate": 130,
      "memo": "SWIFT payment $5000 @ 130"
    }
  ]
}
```

### Advanced Scenarios Handled
- **Cross-Currency:** Post in any currency; system balances in base currency.
- **Inventory/COGS:** Track quantities and average costs across multiple warehouses/items.
- **FX Gain/Loss:** Record realized/unrealized gains from currency fluctuations.
- **Volatile Assets:** Mark-to-market revaluation for gold, commodities, or forex.
- **Delayed Payments:** Track receivables/payables with changing exchange rates.

If debits ≠ credits → 422 error. Always.

---

## The Immutable Rules

1. Every transaction balances (enforced at API + DB level)
2. Once posted, entries never change — corrections = reversal + new transaction
3. Every entry is either debit OR credit, never both
4. Balances are always calculated from entries, never stored
5. Inventory quantity = sum of movements

---

## The Golden Rule Check

```
GET /api/v1/reports/verify-balance?tenant_id=<your-tenant-id>
```

Returns:
```json
{
  "total_debits": 1234567.00,
  "total_credits": 1234567.00,
  "imbalance": 0.00,
  "is_balanced": true,
  "verdict": "✅ BALANCED"
}
```

Run this any time. If it ever says ❌, something at the DB level has been corrupted outside the API. It shouldn't be possible, but now you'll know immediately.

# Universal Double-Entry Ledger
## Phase 1 – The Truth Layer

**Stack:** Supabase (PostgreSQL) + Python + FastAPI  
**Philosophy:** Log any mess accurately now. Unlock infinite possibilities later.

---

## Setup

### 1. Supabase
1. Create a new Supabase project at supabase.com
2. Go to **SQL Editor** and run `schema.sql` in full
3. Copy your **direct connection string** (Settings → Database → Connection String → URI)
   - Use the **direct** connection, not the pooler, for Phase 1

### 2. Environment
```bash
cp .env.example .env
# Edit .env with your DATABASE_URL
```

`.env`:
```
DATABASE_URL=postgresql://postgres.[ref]:[password]@db.[ref].supabase.co:5432/postgres
```

### 3. Install & Run
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs  
Truth check: http://localhost:8000/api/v1/reports/verify-balance

### 4. Run Tests (no DB needed)
```bash
pytest tests/test_truth.py -v
```

---

## File Structure

```
schema.sql          ← Run once in Supabase SQL editor
main.py             ← FastAPI app entry point
db.py               ← Supabase connection pool
models.py           ← Pydantic models (truth in Python)
routes.py           ← All API endpoints
requirements.txt    ← Dependencies
tests/
  test_truth.py     ← Truth verification tests (no DB needed)
```

---

## Key Endpoints

| Method | Path | What it does |
|--------|------|--------------|
| POST | `/api/v1/transactions` | Create + post a balanced transaction |
| GET  | `/api/v1/transactions` | List transactions |
| POST | `/api/v1/transactions/{id}/reverse` | Reverse a posted transaction |
| GET  | `/api/v1/ledger` | Browse entries by any dimension |
| GET  | `/api/v1/reports/trial-balance` | Full trial balance |
| GET  | `/api/v1/reports/party-balances` | Who owes what |
| GET  | `/api/v1/reports/currency-exposure` | Forex positions |
| GET  | `/api/v1/reports/verify-balance` | **The truth check** |
| POST | `/api/v1/accounts` | Create account |
| POST | `/api/v1/parties` | Create party |
| POST | `/api/v1/inventory` | Create inventory item |

---

## How to Record a Transaction

Every real-world event is just entries + context:

```json
POST /api/v1/transactions
{
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "date": "2024-01-15",
  "description": "Import 100 phones from Shenzhen",
  "entries": [
    {
      "account_id": "<inventory-account-id>",
      "debit_amount": 650000,
      "currency_code": "KES",
      "exchange_rate": 1,
      "inventory_item_id": "<phones-item-id>",
      "quantity": 100,
      "tags": ["china-import", "phones"]
    },
    {
      "account_id": "<bank-usd-account-id>",
      "credit_amount": 5000,
      "currency_code": "USD",
      "exchange_rate": 130,
      "memo": "SWIFT payment $5000 @ 130"
    }
  ]
}
```

### Advanced Scenarios Handled
- **Cross-Currency:** Post in any currency; system balances in base currency.
- **Inventory/COGS:** Track quantities and average costs across multiple warehouses/items.
- **FX Gain/Loss:** Record realized/unrealized gains from currency fluctuations.
- **Volatile Assets:** Mark-to-market revaluation for gold, commodities, or forex.
- **Delayed Payments:** Track receivables/payables with changing exchange rates.

If debits ≠ credits → 422 error. Always.

---

## The Immutable Rules

1. Every transaction balances (enforced at API + DB level)
2. Once posted, entries never change — corrections = reversal + new transaction
3. Every entry is either debit OR credit, never both
4. Balances are always calculated from entries, never stored
5. Inventory quantity = sum of movements

---

## The Golden Rule Check

```
GET /api/v1/reports/verify-balance?tenant_id=<your-tenant-id>
```

Returns:
```json
{
  "total_debits": 1234567.00,
  "total_credits": 1234567.00,
  "imbalance": 0.00,
  "is_balanced": true,
  "verdict": "✅ BALANCED"
}
```

Run this any time. If it ever says ❌, something at the DB level has been corrupted outside the API. It shouldn't be possible, but now you'll know immediately.

---

## Deployment (Railway / Render / Heroku)

This repo is deployment-ready. Options:

### A) Railway (recommended)
- Make sure you have a running Supabase project and your `.env` like `.env.example` (Pooler creds, SSL required).
- Add a new Railway project from this repo.
- Add Environment Variables (from `.env.example`):
  - `user`, `password`, `host`, `port=6543`, `dbname`
  - Optional: `DEFAULT_TENANT_ID`
- Railway detects `Procfile`:
  - `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set service port to `PORT` provided by Railway (default).
- CORS: In `main.py`, CORS is open (`*`) for now; restrict `allow_origins` in production.

### B) Heroku
- `heroku create`
- `heroku config:set user=... password=... host=... port=6543 dbname=postgres`
- `git push heroku main`

### C) Docker (optional)
Create a minimal `Dockerfile` if you prefer container deploys:
```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Expose port 8000 and set the same environment vars as above.

### Database Migrations
- Run `schema.sql` once in Supabase SQL Editor (already aligned with the current source: base-currency balance check + correct reversals for inventory).
- No ORM migrations are required (pure SQL schema).

### Health & Observability
- Health: `GET /health` returns `{ "status": "ok" }`.
- OpenAPI: `GET /openapi.json` and Swagger UI `/docs`.
- Logs: Uvicorn stdout; `main.py` includes a lightweight DB connectivity check on startup.

---

## Frontend Handover
See `handover/frontend_guide.md` for:
- Posting transactions (examples in JS/TS)
- Reversals
- Useful reporting endpoints and how to map them into UI widgets

---

## Tests
- Unit tests (no DB): `pytest test_truth.py -v` (26 passing)
- Notes: Pydantic v2 emits deprecation warnings for class-based config; this does not affect behavior now.

---

## Production Checklist
- [ ] Set real CORS origins in `main.py` (`allow_origins=["https://your-frontend.app"]`)
- [ ] Use Supabase Pooler for app traffic (SSL required); direct connection only for heavy DDL/maintenance
- [ ] Rotate DB passwords and store in platform secrets manager
- [ ] Monitor `GET /api/v1/reports/verify-balance` periodically for system health
- [ ] Backups enabled on Supabase
