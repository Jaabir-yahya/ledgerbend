"""
models.py - Pydantic models for the double-entry ledger.
These mirror the database schema exactly.
Every field matches the DB column. No surprises.
"""
from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator
import enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class AccountType(str, enum.Enum):
    asset     = "asset"
    liability = "liability"
    equity    = "equity"
    income    = "income"
    expense   = "expense"


class NormalBalance(str, enum.Enum):
    debit  = "debit"
    credit = "credit"


class PartyType(str, enum.Enum):
    customer = "customer"
    supplier = "supplier"
    agent    = "agent"
    runner   = "runner"
    partner  = "partner"
    other    = "other"


# ─── Tenants ──────────────────────────────────────────────────────────────────

class TenantCreate(BaseModel):
    name: str
    base_currency: str = "KES"
    settings: dict = {}

    model_config = {"from_attributes": True}


class Tenant(TenantCreate):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Accounts ─────────────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    tenant_id: UUID
    code: str
    name: str
    type: AccountType
    normal_balance: NormalBalance
    parent_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class Account(AccountCreate):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Parties ──────────────────────────────────────────────────────────────────

class PartyCreate(BaseModel):
    tenant_id: UUID
    name: str
    type: Optional[PartyType] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    metadata: dict = {}

    model_config = {"from_attributes": True}


class Party(PartyCreate):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Inventory Items ──────────────────────────────────────────────────────────

class InventoryItemCreate(BaseModel):
    tenant_id: UUID
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    unit_type: str = "piece"
    is_volatile: bool = False

    model_config = {"from_attributes": True}


class InventoryItem(InventoryItemCreate):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Journal Entry ────────────────────────────────────────────────────────────

class JournalEntryCreate(BaseModel):
    """
    One leg of a transaction. Must be either debit OR credit, never both.
    The validator enforces this at the API layer before it even hits the DB.
    """
    account_id: UUID
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")

    party_id: Optional[UUID] = None

    inventory_item_id: Optional[UUID] = None
    quantity: Optional[Decimal] = None

    currency_code: str = "KES"
    exchange_rate: Decimal = Decimal("1.0")

    memo: Optional[str] = None
    tags: List[str] = []
    metadata: dict = {}

    @model_validator(mode="after")
    def validate_direction(self) -> "JournalEntryCreate":
        d = self.debit_amount
        c = self.credit_amount
        if d > 0 and c > 0:
            raise ValueError("A journal entry cannot have both debit and credit amounts.")
        if d == 0 and c == 0:
            raise ValueError("A journal entry must have either a debit or credit amount.")
        if d < 0 or c < 0:
            raise ValueError("Amounts must be positive. Direction is determined by debit/credit field.")
        if self.exchange_rate <= 0:
            raise ValueError("Exchange rate must be positive.")
        if self.inventory_item_id and self.quantity is None:
            raise ValueError("quantity is required when inventory_item_id is set.")
        if self.quantity and not self.inventory_item_id:
            raise ValueError("inventory_item_id is required when quantity is set.")
        return self

    @property
    def amount(self) -> Decimal:
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount

    @property
    def compute_base_amount(self) -> Decimal:
        return self.amount * self.exchange_rate

    @property
    def direction(self) -> str:
        return "debit" if self.debit_amount > 0 else "credit"


class JournalEntry(JournalEntryCreate):
    id: UUID
    tenant_id: UUID
    transaction_id: UUID
    # base_amount is computed in parent, but stored in DB
    base_amount: Decimal 
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Inventory Movement ───────────────────────────────────────────────────────

class InventoryMovementCreate(BaseModel):
    journal_entry_id: UUID
    inventory_item_id: UUID
    quantity_change: Decimal   # positive = stock in, negative = stock out
    unit_cost: Optional[Decimal] = None


class InventoryMovement(InventoryMovementCreate):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Transaction ──────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    """
    A transaction groups ≥2 journal entries that must balance.
    Submit entries together. The API will validate balance before posting.
    """
    tenant_id: UUID
    transaction_number: Optional[str] = None  # auto-generated if not provided
    date: date
    description: Optional[str] = None
    reference: Optional[str] = None
    entries: List[JournalEntryCreate] = Field(..., min_length=2)

    @model_validator(mode="after")
    def validate_balance(self) -> "TransactionCreate":
        total_debit  = sum(e.compute_base_amount for e in self.entries if e.direction == "debit")
        total_credit = sum(e.compute_base_amount for e in self.entries if e.direction == "credit")
        diff = abs(total_debit - total_credit)
        if diff > Decimal("0.01"):
            raise ValueError(
                f"Transaction does not balance in base currency. "
                f"Debits (base): {total_debit}, Credits (base): {total_credit}, "
                f"Difference: {diff}"
            )
        return self


class TransactionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    transaction_number: str
    date: date
    description: Optional[str]
    reference: Optional[str]
    is_posted: bool
    is_reversal: bool
    reverses_transaction_id: Optional[UUID]
    created_at: datetime
    posted_at: Optional[datetime]
    entries: List[JournalEntry] = []

    model_config = {"from_attributes": True}


# ─── Reversal Request ─────────────────────────────────────────────────────────

class ReversalRequest(BaseModel):
    date: date
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Query / Filter Models ────────────────────────────────────────────────────

class JournalFilter(BaseModel):
    """Flexible filter for browsing the ledger by any dimension."""
    tenant_id: UUID
    account_id: Optional[UUID] = None
    party_id: Optional[UUID] = None
    inventory_item_id: Optional[UUID] = None
    currency_code: Optional[str] = None
    tag: Optional[str] = None           # filter entries containing this tag
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    posted_only: bool = True
    limit: int = Field(100, le=1000)
    offset: int = 0

    model_config = {"from_attributes": True}


# ─── Response Wrappers ────────────────────────────────────────────────────────

class TrialBalanceRow(BaseModel):
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    normal_balance: str
    total_debits: Decimal
    total_credits: Decimal
    total_base: Decimal
    net_balance: Decimal

    model_config = {"from_attributes": True}


class PartyBalanceRow(BaseModel):
    party_id: UUID
    party_name: str
    party_type: Optional[str]
    total_debits: Decimal
    total_credits: Decimal
    net_balance_base: Decimal

    model_config = {"from_attributes": True}


class InventoryPosition(BaseModel):
    item_id: UUID
    item_name: str
    sku: Optional[str]
    unit_type: str
    quantity_on_hand: Decimal
    avg_unit_cost: Decimal

    model_config = {"from_attributes": True}


class CurrencyExposure(BaseModel):
    currency_code: str
    total_debits: Decimal
    total_credits: Decimal
    net_position: Decimal

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
    id: Optional[UUID] = None


# =====================================================
# FINANCIAL STATEMENT RESPONSE MODELS
# =====================================================

class IncomeStatementRow(BaseModel):
    tenant_id: UUID
    account_type: str
    account_code: str
    account_name: str
    total_debits: Decimal
    total_credits: Decimal
    net_amount: Decimal

    model_config = {"from_attributes": True}


class IncomeStatementSummary(BaseModel):
    tenant_id: UUID
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    profit_margin: Decimal
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    is_profitable: bool


class BalanceSheetRow(BaseModel):
    tenant_id: UUID
    account_type: str
    account_code: str
    account_name: str
    normal_balance: str
    balance: Decimal

    model_config = {"from_attributes": True}


class BalanceSheetSummary(BaseModel):
    tenant_id: UUID
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    is_balanced: bool
    as_of_date: Optional[date] = None


class CashFlowRow(BaseModel):
    tenant_id: UUID
    date: Optional[date] = None
    account_type: str
    account_code: str
    account_name: str
    total_debits: Decimal
    total_credits: Decimal
    flow_category: str

    model_config = {"from_attributes": True}


class CashFlowSummary(BaseModel):
    tenant_id: UUID
    cash_from_operating: Decimal
    cash_from_investing: Decimal
    cash_from_financing: Decimal
    net_cash_change: Decimal
    period_from: Optional[date] = None
    period_to: Optional[date] = None
