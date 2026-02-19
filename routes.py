"""
routes.py - All API routes for the double-entry ledger.
Organized by resource. Each route is thin - validation in models,
business logic in DB functions.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from db import get_db
from models import (
    Account, AccountCreate,
    Party, PartyCreate,
    InventoryItem, InventoryItemCreate,
    InventoryMovementCreate,
    TransactionCreate, TransactionResponse,
    ReversalRequest,
    JournalFilter,
    TrialBalanceRow, PartyBalanceRow, InventoryPosition, CurrencyExposure,
    MessageResponse,
)

router = APIRouter()


# ─── Utility ──────────────────────────────────────────────────────────────────

def row_to_dict(row) -> dict:
    """Convert asyncpg Record to dict."""
    if not row:
        return {}
    d = dict(row)
    # Convert JSONB strings back to dict/list if they are strings
    import json
    for key in ["metadata", "tags", "settings"]:
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except:
                pass
    return d


def generate_txn_number(prefix: str = "TXN") -> str:
    """Generate a unique transaction number."""
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    uid = str(uuid4())[:8].upper()
    return f"{prefix}-{ts}-{uid}"


def http_error(status: int, detail: str):
    raise HTTPException(status_code=status, detail=detail)


# ─── ACCOUNTS ─────────────────────────────────────────────────────────────────

@router.post("/accounts", response_model=Account, tags=["Accounts"])
async def create_account(payload: AccountCreate, db=Depends(get_db)):
    """Create a new account in the chart of accounts."""
    try:
        row = await db.fetchrow("""
            INSERT INTO accounts (tenant_id, code, name, type, normal_balance, parent_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """, payload.tenant_id, payload.code, payload.name,
             payload.type.value, payload.normal_balance.value, payload.parent_id)
        return Account(**row_to_dict(row))
    except asyncpg.UniqueViolationError:
        http_error(409, f"Account code '{payload.code}' already exists for this tenant.")


@router.get("/accounts", response_model=List[Account], tags=["Accounts"])
async def list_accounts(tenant_id: UUID, db=Depends(get_db)):
    """List all accounts for a tenant."""
    rows = await db.fetch(
        "SELECT * FROM accounts WHERE tenant_id = $1 AND is_active = true ORDER BY code",
        tenant_id
    )
    return [Account(**row_to_dict(r)) for r in rows]


@router.get("/accounts/{account_id}", response_model=Account, tags=["Accounts"])
async def get_account(account_id: UUID, db=Depends(get_db)):
    row = await db.fetchrow("SELECT * FROM accounts WHERE id = $1", account_id)
    if not row:
        http_error(404, "Account not found.")
    return Account(**row_to_dict(row))


# ─── PARTIES ──────────────────────────────────────────────────────────────────

@router.post("/parties", response_model=Party, tags=["Parties"])
async def create_party(payload: PartyCreate, db=Depends(get_db)):
    """Create a party: customer, supplier, runner, agent, etc."""
    import json
    row = await db.fetchrow("""
        INSERT INTO parties (tenant_id, name, type, email, phone, address, tax_id, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """, payload.tenant_id, payload.name,
         payload.type.value if payload.type else None,
         payload.email, payload.phone, payload.address, payload.tax_id,
         json.dumps(payload.metadata))
    return Party(**row_to_dict(row))


@router.get("/parties", response_model=List[Party], tags=["Parties"])
async def list_parties(
    tenant_id: UUID,
    type: Optional[str] = None,
    db=Depends(get_db)
):
    """List parties, optionally filtered by type."""
    if type:
        rows = await db.fetch(
            "SELECT * FROM parties WHERE tenant_id = $1 AND type = $2 AND is_active = true ORDER BY name",
            tenant_id, type
        )
    else:
        rows = await db.fetch(
            "SELECT * FROM parties WHERE tenant_id = $1 AND is_active = true ORDER BY name",
            tenant_id
        )
    return [Party(**row_to_dict(r)) for r in rows]


@router.get("/parties/{party_id}", response_model=Party, tags=["Parties"])
async def get_party(party_id: UUID, db=Depends(get_db)):
    row = await db.fetchrow("SELECT * FROM parties WHERE id = $1", party_id)
    if not row:
        http_error(404, "Party not found.")
    return Party(**row_to_dict(row))


# ─── INVENTORY ITEMS ──────────────────────────────────────────────────────────

@router.post("/inventory", response_model=InventoryItem, tags=["Inventory"])
async def create_inventory_item(payload: InventoryItemCreate, db=Depends(get_db)):
    """Create a trackable inventory item (phones, gold, coffee, etc.)."""
    try:
        row = await db.fetchrow("""
            INSERT INTO inventory_items (tenant_id, name, sku, description, unit_type, is_volatile)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """, payload.tenant_id, payload.name, payload.sku,
             payload.description, payload.unit_type, payload.is_volatile)
        return InventoryItem(**row_to_dict(row))
    except asyncpg.UniqueViolationError:
        http_error(409, f"SKU '{payload.sku}' already exists for this tenant.")


@router.get("/inventory", response_model=List[InventoryItem], tags=["Inventory"])
async def list_inventory_items(tenant_id: UUID, db=Depends(get_db)):
    rows = await db.fetch(
        "SELECT * FROM inventory_items WHERE tenant_id = $1 AND is_active = true ORDER BY name",
        tenant_id
    )
    return [InventoryItem(**row_to_dict(r)) for r in rows]


@router.get("/inventory/positions", response_model=List[InventoryPosition], tags=["Inventory"])
async def get_inventory_positions(tenant_id: UUID, db=Depends(get_db)):
    """Current stock levels and average costs for all items."""
    rows = await db.fetch(
        "SELECT * FROM inventory_positions WHERE tenant_id = $1",
        tenant_id
    )
    return [InventoryPosition(**row_to_dict(r)) for r in rows]


# ─── TRANSACTIONS (the main event) ────────────────────────────────────────────

@router.post("/transactions", response_model=TransactionResponse, tags=["Transactions"])
async def create_and_post_transaction(payload: TransactionCreate, db=Depends(get_db)):
    """
    Create a balanced transaction with all its journal entries.
    Validates balance at the Pydantic level AND at the DB level.
    If balance passes, posts immediately (immutable from this point).

    This is the primary endpoint. Everything flows through here.
    """
    import json

    txn_number = payload.transaction_number or generate_txn_number()

    async with db.transaction():
        # 1. Create the transaction (draft)
        try:
            txn_row = await db.fetchrow("""
                INSERT INTO transactions (tenant_id, transaction_number, date, description, reference, is_posted)
                VALUES ($1, $2, $3, $4, $5, false)
                RETURNING *
            """, payload.tenant_id, txn_number, payload.date,
                 payload.description, payload.reference)
        except asyncpg.UniqueViolationError:
            http_error(409, f"Transaction number '{txn_number}' already exists.")

        txn_id = txn_row["id"]
        created_entries = []

        # 2. Insert all journal entries
        for entry in payload.entries:
            entry_row = await db.fetchrow("""
                INSERT INTO journal_entries (
                    tenant_id, transaction_id, account_id,
                    debit_amount, credit_amount,
                    party_id, inventory_item_id, quantity,
                    currency_code, exchange_rate,
                    memo, tags, metadata
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                RETURNING *
            """,
                payload.tenant_id, txn_id, entry.account_id,
                float(entry.debit_amount), float(entry.credit_amount),
                entry.party_id, entry.inventory_item_id,
                float(entry.quantity) if entry.quantity else None,
                entry.currency_code, float(entry.exchange_rate),
                entry.memo, json.dumps(entry.tags), json.dumps(entry.metadata)
            )
            created_entries.append(dict(entry_row))

            # 3. If inventory item, create movement record
            if entry.inventory_item_id and entry.quantity:
                # debit = stock in (positive), credit = stock out (negative)
                qty_change = float(entry.quantity) if entry.debit_amount > 0 else -float(entry.quantity)
                unit_cost = float(entry.compute_base_amount / entry.quantity) if entry.quantity else None

                await db.execute("""
                    INSERT INTO inventory_movements
                        (journal_entry_id, inventory_item_id, quantity_change, unit_cost)
                    VALUES ($1, $2, $3, $4)
                """, entry_row["id"], entry.inventory_item_id, qty_change, unit_cost)

        # 4. Post the transaction (DB validates balance one final time)
        try:
            await db.execute("SELECT post_transaction($1)", txn_id)
        except asyncpg.exceptions.RaiseException as e:
            http_error(422, str(e))

    # 5. Return full transaction with entries
    return await _get_transaction_full(txn_id, db)


@router.get("/transactions", response_model=List[TransactionResponse], tags=["Transactions"])
async def list_transactions(
    tenant_id: UUID,
    posted_only: bool = True,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db=Depends(get_db)
):
    """List transactions with optional date range filter."""
    query = """
        SELECT * FROM transactions
        WHERE tenant_id = $1
        {posted_filter}
        {date_from_filter}
        {date_to_filter}
        ORDER BY date DESC, created_at DESC
        LIMIT $2 OFFSET $3
    """
    conditions = []
    params = [tenant_id, limit, offset]

    q = "SELECT * FROM transactions WHERE tenant_id = $1"
    if posted_only:
        q += " AND is_posted = true"
    if date_from:
        params.append(date_from)
        q += f" AND date >= ${len(params)}"
    if date_to:
        params.append(date_to)
        q += f" AND date <= ${len(params)}"
    q += f" ORDER BY date DESC, created_at DESC LIMIT $2 OFFSET $3"

    rows = await db.fetch(q, *params)
    result = []
    for row in rows:
        txn = await _get_transaction_full(row["id"], db)
        result.append(txn)
    return result


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse, tags=["Transactions"])
async def get_transaction(transaction_id: UUID, db=Depends(get_db)):
    row = await db.fetchrow("SELECT * FROM transactions WHERE id = $1", transaction_id)
    if not row:
        http_error(404, "Transaction not found.")
    return await _get_transaction_full(transaction_id, db)


@router.post("/transactions/{transaction_id}/reverse", response_model=TransactionResponse, tags=["Transactions"])
async def reverse_transaction(
    transaction_id: UUID,
    payload: ReversalRequest,
    db=Depends(get_db)
):
    """
    Reverse a posted transaction. Creates a new balanced transaction
    with all entries flipped. This is the only way to correct a posted entry.
    """
    try:
        new_txn_id = await db.fetchval(
            "SELECT reverse_transaction($1, $2, $3)",
            transaction_id, payload.date, payload.description
        )
    except asyncpg.exceptions.RaiseException as e:
        http_error(422, str(e))

    return await _get_transaction_full(new_txn_id, db)


# ─── JOURNAL LEDGER (browse by any dimension) ─────────────────────────────────

@router.get("/ledger", tags=["Ledger"])
async def browse_ledger(
    tenant_id: UUID,
    account_id: Optional[UUID] = None,
    party_id: Optional[UUID] = None,
    inventory_item_id: Optional[UUID] = None,
    currency_code: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    posted_only: bool = True,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db=Depends(get_db)
):
    """
    Browse the raw ledger. Filter by any dimension.
    This is the query engine - every hop is findable from here.
    """
    conditions = ["je.tenant_id = $1"]
    params = [tenant_id]

    def add(cond: str, val):
        params.append(val)
        conditions.append(cond.format(n=len(params)))

    if posted_only:
        conditions.append("t.is_posted = true")
    if account_id:
        add("je.account_id = ${n}", account_id)
    if party_id:
        add("je.party_id = ${n}", party_id)
    if inventory_item_id:
        add("je.inventory_item_id = ${n}", inventory_item_id)
    if currency_code:
        add("je.currency_code = ${n}", currency_code)
    if tag:
        add("je.tags @> ${n}::jsonb", f'["{tag}"]')
    if date_from:
        add("t.date >= ${n}", date_from)
    if date_to:
        add("t.date <= ${n}", date_to)

    where = " AND ".join(conditions)
    params.extend([limit, offset])
    n_limit = len(params) - 1
    n_offset = len(params)

    query = f"""
        SELECT
            je.*,
            t.date, t.description AS txn_description, t.transaction_number,
            a.code AS account_code, a.name AS account_name,
            p.name AS party_name
        FROM journal_entries je
        JOIN transactions t ON t.id = je.transaction_id
        JOIN accounts a ON a.id = je.account_id
        LEFT JOIN parties p ON p.id = je.party_id
        WHERE {where}
        ORDER BY t.date DESC, je.created_at DESC
        LIMIT ${n_limit} OFFSET ${n_offset}
    """

    rows = await db.fetch(query, *params)
    return [dict(r) for r in rows]


# ─── REPORTING VIEWS ──────────────────────────────────────────────────────────

@router.get("/reports/trial-balance", response_model=List[TrialBalanceRow], tags=["Reports"])
async def trial_balance(tenant_id: UUID, db=Depends(get_db)):
    """Full trial balance - every account's net position."""
    rows = await db.fetch(
        "SELECT * FROM trial_balance WHERE tenant_id = $1 ORDER BY account_code",
        tenant_id
    )
    return [TrialBalanceRow(**row_to_dict(r)) for r in rows]


@router.get("/reports/party-balances", response_model=List[PartyBalanceRow], tags=["Reports"])
async def party_balances(tenant_id: UUID, db=Depends(get_db)):
    """Net balance per party - who owes what."""
    rows = await db.fetch(
        "SELECT * FROM party_balances WHERE tenant_id = $1 ORDER BY party_name",
        tenant_id
    )
    return [PartyBalanceRow(**row_to_dict(r)) for r in rows]


@router.get("/reports/currency-exposure", response_model=List[CurrencyExposure], tags=["Reports"])
async def currency_exposure(tenant_id: UUID, db=Depends(get_db)):
    """Net position in each currency - critical for forex traders."""
    rows = await db.fetch(
        "SELECT * FROM currency_exposure WHERE tenant_id = $1 ORDER BY currency_code",
        tenant_id
    )
    return [CurrencyExposure(**row_to_dict(r)) for r in rows]


@router.get("/reports/verify-balance", tags=["Reports"])
async def verify_system_balance(tenant_id: UUID, db=Depends(get_db)):
    """
    The golden rule check: total debits must equal total credits across all
    posted transactions. If this ever returns non-zero, something is very wrong.
    This is your truth test - run it any time.
    """
    row = await db.fetchrow("""
        SELECT
            SUM(debit_amount)  AS total_debits,
            SUM(credit_amount) AS total_credits,
            ABS(SUM(debit_amount) - SUM(credit_amount)) AS imbalance
        FROM journal_entries je
        JOIN transactions t ON t.id = je.transaction_id
        WHERE je.tenant_id = $1 AND t.is_posted = true
    """, tenant_id)

    return {
        "total_debits":  float(row["total_debits"] or 0),
        "total_credits": float(row["total_credits"] or 0),
        "imbalance":     float(row["imbalance"] or 0),
        "is_balanced":   float(row["imbalance"] or 0) <= 0.01,
        "verdict":       "✅ BALANCED" if float(row["imbalance"] or 0) <= 0.01 else "❌ OUT OF BALANCE"
    }


# ─── INTERNAL HELPER ──────────────────────────────────────────────────────────

async def _get_transaction_full(transaction_id: UUID, db) -> TransactionResponse:
    """Fetch a transaction with all its journal entries."""
    txn_row = await db.fetchrow("SELECT * FROM transactions WHERE id = $1", transaction_id)
    if not txn_row:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    entry_rows = await db.fetch(
        "SELECT * FROM journal_entries WHERE transaction_id = $1 ORDER BY created_at",
        transaction_id
    )

    txn_data = row_to_dict(txn_row)
    txn_data["entries"] = [row_to_dict(r) for r in entry_rows]
    return TransactionResponse(**txn_data)
