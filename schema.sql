-- =====================================================
-- UNIVERSAL DOUBLE-ENTRY LEDGER - SUPABASE SCHEMA
-- Phase 1: Solo developer, single tenant, truth layer
-- =====================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- CORE TABLES
-- =====================================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    base_currency VARCHAR(3) DEFAULT 'KES',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('asset', 'liability', 'equity', 'income', 'expense')),
    normal_balance VARCHAR(10) NOT NULL CHECK (normal_balance IN ('debit', 'credit')),
    parent_id UUID REFERENCES accounts(id),  -- for account hierarchy
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE TABLE parties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('customer', 'supplier', 'agent', 'runner', 'partner', 'other')),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    tax_id VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    description TEXT,
    unit_type VARCHAR(50) DEFAULT 'piece',  -- kg, piece, box, container, gram
    is_volatile BOOLEAN DEFAULT false,       -- price changes often (gold, forex)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, sku)
);

-- =====================================================
-- TRANSACTION TABLES
-- =====================================================

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    transaction_number VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    reference VARCHAR(255),   -- M-PESA ID, SWIFT#, invoice#, waybill#
    is_posted BOOLEAN DEFAULT false,  -- false = draft, true = immutable
    is_reversal BOOLEAN DEFAULT false,
    reverses_transaction_id UUID REFERENCES transactions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    posted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(tenant_id, transaction_number)
);

CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,

    -- Core accounting
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    debit_amount NUMERIC(20,4) DEFAULT 0 CHECK (debit_amount >= 0),
    credit_amount NUMERIC(20,4) DEFAULT 0 CHECK (credit_amount >= 0),

    -- WHO
    party_id UUID REFERENCES parties(id),

    -- WHAT (inventory)
    inventory_item_id UUID REFERENCES inventory_items(id),
    quantity NUMERIC(20,4),

    -- CURRENCY (per entry - critical for imports/exports/forex)
    currency_code VARCHAR(3) NOT NULL DEFAULT 'KES',
    exchange_rate NUMERIC(20,6) DEFAULT 1.0 CHECK (exchange_rate > 0),
    -- base_amount = amount in tenant's base currency
    base_amount NUMERIC(20,4) GENERATED ALWAYS AS (
        CASE
            WHEN debit_amount > 0 THEN debit_amount * exchange_rate
            ELSE credit_amount * exchange_rate
        END
    ) STORED,

    -- CONTEXT
    memo TEXT,
    tags JSONB DEFAULT '[]',      -- ["runner", "container-123", "dubai-gold"]
    metadata JSONB DEFAULT '{}',  -- future extensions

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- CONSTRAINTS
    CONSTRAINT one_direction CHECK (
        (debit_amount > 0 AND credit_amount = 0) OR
        (credit_amount > 0 AND debit_amount = 0)
    ),
    CONSTRAINT quantity_requires_item CHECK (
        (inventory_item_id IS NULL AND quantity IS NULL) OR
        (inventory_item_id IS NOT NULL AND quantity IS NOT NULL)
    )
);

CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE RESTRICT,
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE RESTRICT,
    quantity_change NUMERIC(20,4) NOT NULL,  -- positive = in, negative = out
    unit_cost NUMERIC(20,4),                 -- cost per unit in base currency at time of movement
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    transaction_id UUID REFERENCES transactions(id),
    journal_entry_id UUID REFERENCES journal_entries(id),
    filename VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50),
    description TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================

CREATE INDEX idx_journal_tenant_date ON journal_entries(tenant_id, created_at DESC);
CREATE INDEX idx_journal_transaction ON journal_entries(transaction_id);
CREATE INDEX idx_journal_account ON journal_entries(account_id);
CREATE INDEX idx_journal_party ON journal_entries(party_id) WHERE party_id IS NOT NULL;
CREATE INDEX idx_journal_inventory ON journal_entries(inventory_item_id) WHERE inventory_item_id IS NOT NULL;
CREATE INDEX idx_journal_currency ON journal_entries(currency_code);
CREATE INDEX idx_journal_tags ON journal_entries USING GIN(tags);
CREATE INDEX idx_transactions_tenant_date ON transactions(tenant_id, date DESC);
CREATE INDEX idx_transactions_posted ON transactions(tenant_id, is_posted);
CREATE INDEX idx_inventory_movements_item ON inventory_movements(inventory_item_id);

-- =====================================================
-- BALANCE CHECK FUNCTION
-- Called explicitly on post, not on every insert.
-- This is the correct approach - check when you intend
-- to seal the transaction, not mid-entry.
-- =====================================================

CREATE OR REPLACE FUNCTION check_transaction_balance(p_transaction_id UUID)
RETURNS VOID AS $$
DECLARE
    v_total_debit NUMERIC(20,4);
    v_total_credit NUMERIC(20,4);
    v_diff NUMERIC(20,4);
    v_entry_count INTEGER;
BEGIN
    SELECT
        COALESCE(SUM(base_amount) FILTER (WHERE debit_amount > 0), 0),
        COALESCE(SUM(base_amount) FILTER (WHERE credit_amount > 0), 0),
        COUNT(*)
    INTO v_total_debit, v_total_credit, v_entry_count
    FROM journal_entries
    WHERE transaction_id = p_transaction_id;

    -- Must have at least 2 entries
    IF v_entry_count < 2 THEN
        RAISE EXCEPTION 'Transaction must have at least 2 journal entries. Found: %', v_entry_count;
    END IF;

    -- Round to 4 decimal places before comparison to avoid floating point noise
    v_total_debit := ROUND(v_total_debit, 4);
    v_total_credit := ROUND(v_total_credit, 4);
    v_diff := ABS(v_total_debit - v_total_credit);

    -- Allow 0.01 rounding tolerance in base currency
    IF v_diff > 0.01 THEN
        RAISE EXCEPTION 'Transaction does not balance in base currency. Debits (base): %, Credits (base): %, Difference: %',
            v_total_debit, v_total_credit, v_diff;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- POST TRANSACTION FUNCTION
-- The only way to seal a transaction. Validates balance
-- first. Once posted, entries are immutable.
-- =====================================================

CREATE OR REPLACE FUNCTION post_transaction(p_transaction_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Check it's not already posted
    IF EXISTS (
        SELECT 1 FROM transactions
        WHERE id = p_transaction_id AND is_posted = true
    ) THEN
        RAISE EXCEPTION 'Transaction % is already posted and cannot be modified', p_transaction_id;
    END IF;

    -- Validate balance
    PERFORM check_transaction_balance(p_transaction_id);

    -- Seal it
    UPDATE transactions
    SET is_posted = true,
        posted_at = NOW()
    WHERE id = p_transaction_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PREVENT EDITS TO POSTED TRANSACTIONS
-- =====================================================

CREATE OR REPLACE FUNCTION prevent_posted_modification()
RETURNS TRIGGER AS $$
DECLARE
    v_is_posted BOOLEAN;
BEGIN
    SELECT is_posted INTO v_is_posted
    FROM transactions
    WHERE id = COALESCE(NEW.transaction_id, OLD.transaction_id);

    IF v_is_posted THEN
        RAISE EXCEPTION 'Cannot modify journal entries of a posted transaction. Create a reversal instead.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER guard_posted_entries
    BEFORE UPDATE OR DELETE ON journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION prevent_posted_modification();

-- =====================================================
-- REVERSAL FUNCTION
-- The only correct way to "undo" a posted transaction.
-- Creates a new transaction with all entries flipped.
-- =====================================================

CREATE OR REPLACE FUNCTION reverse_transaction(
    p_transaction_id UUID,
    p_date DATE,
    p_description TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_original transactions%ROWTYPE;
    v_new_txn_id UUID;
    v_new_txn_number VARCHAR(100);
    v_entry journal_entries%ROWTYPE;
    v_rev_entry_id UUID;
    v_orig_unit_cost NUMERIC(20,4);
BEGIN
    -- Get original transaction
    SELECT * INTO v_original FROM transactions WHERE id = p_transaction_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transaction % not found', p_transaction_id;
    END IF;

    IF NOT v_original.is_posted THEN
        RAISE EXCEPTION 'Can only reverse posted transactions';
    END IF;

    -- Generate reversal number
    v_new_txn_number := 'REV-' || v_original.transaction_number;

    -- Create reversal transaction
    INSERT INTO transactions (
        tenant_id, transaction_number, date, description,
        reference, is_reversal, reverses_transaction_id
    ) VALUES (
        v_original.tenant_id,
        v_new_txn_number,
        p_date,
        COALESCE(p_description, 'Reversal of: ' || COALESCE(v_original.description, v_original.transaction_number)),
        v_original.reference,
        true,
        p_transaction_id
    ) RETURNING id INTO v_new_txn_id;

    -- Copy all entries with debits/credits flipped
    FOR v_entry IN
        SELECT * FROM journal_entries WHERE transaction_id = p_transaction_id
    LOOP
        -- Insert flipped journal entry
        INSERT INTO journal_entries (
            tenant_id, transaction_id, account_id,
            debit_amount, credit_amount,
            party_id, inventory_item_id, quantity,
            currency_code, exchange_rate,
            memo, tags, metadata
        ) VALUES (
            v_entry.tenant_id, v_new_txn_id, v_entry.account_id,
            v_entry.credit_amount,   -- FLIP
            v_entry.debit_amount,    -- FLIP
            v_entry.party_id, v_entry.inventory_item_id, 
            v_entry.quantity,        -- Keep absolute quantity (direction controlled by movement)
            v_entry.currency_code, v_entry.exchange_rate,
            'REVERSAL: ' || COALESCE(v_entry.memo, ''), v_entry.tags, v_entry.metadata
        ) RETURNING id INTO v_rev_entry_id;

        -- If inventory movement exists for the original entry, reverse it too
        IF v_entry.inventory_item_id IS NOT NULL AND v_entry.quantity IS NOT NULL THEN
            -- Find original unit cost
            SELECT unit_cost INTO v_orig_unit_cost 
            FROM inventory_movements 
            WHERE journal_entry_id = v_entry.id;

            INSERT INTO inventory_movements (
                journal_entry_id, inventory_item_id, quantity_change, unit_cost
            ) VALUES (
                v_rev_entry_id, 
                v_entry.inventory_item_id, 
                -- If original was debit (qty_change > 0), reversal is negative. 
                -- If original was credit (qty_change < 0), reversal is positive.
                CASE WHEN v_entry.debit_amount > 0 THEN -v_entry.quantity ELSE v_entry.quantity END,
                v_orig_unit_cost
            );
        END IF;
    END LOOP;

    -- Auto-post the reversal (it's already balanced by definition)
    PERFORM post_transaction(v_new_txn_id);

    RETURN v_new_txn_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS
-- =====================================================

-- Trial balance: what every account owes/holds
CREATE VIEW trial_balance AS
SELECT
    je.tenant_id,
    a.id AS account_id,
    a.code AS account_code,
    a.name AS account_name,
    a.type AS account_type,
    a.normal_balance,
    COALESCE(SUM(je.debit_amount), 0)  AS total_debits,
    COALESCE(SUM(je.credit_amount), 0) AS total_credits,
    COALESCE(SUM(je.base_amount), 0)   AS total_base,
    -- Net balance respecting normal balance direction
    CASE a.normal_balance
        WHEN 'debit'  THEN COALESCE(SUM(je.debit_amount), 0) - COALESCE(SUM(je.credit_amount), 0)
        WHEN 'credit' THEN COALESCE(SUM(je.credit_amount), 0) - COALESCE(SUM(je.debit_amount), 0)
    END AS net_balance
FROM journal_entries je
JOIN transactions t ON t.id = je.transaction_id AND t.is_posted = true
JOIN accounts a ON a.id = je.account_id
GROUP BY je.tenant_id, a.id, a.code, a.name, a.type, a.normal_balance;

-- Party balances: what each party owes or is owed
CREATE VIEW party_balances AS
SELECT
    je.tenant_id,
    p.id AS party_id,
    p.name AS party_name,
    p.type AS party_type,
    COALESCE(SUM(je.debit_amount), 0)  AS total_debits,
    COALESCE(SUM(je.credit_amount), 0) AS total_credits,
    COALESCE(SUM(
        CASE WHEN je.debit_amount > 0 THEN je.base_amount ELSE -je.base_amount END
    ), 0) AS net_balance_base
FROM journal_entries je
JOIN transactions t ON t.id = je.transaction_id AND t.is_posted = true
JOIN parties p ON p.id = je.party_id
WHERE je.party_id IS NOT NULL
GROUP BY je.tenant_id, p.id, p.name, p.type;

-- Inventory positions: current stock levels
CREATE VIEW inventory_positions AS
SELECT
    ii.tenant_id,
    ii.id AS item_id,
    ii.name AS item_name,
    ii.sku,
    ii.unit_type,
    COALESCE(SUM(im.quantity_change), 0) AS quantity_on_hand,
    COALESCE(
        SUM(im.quantity_change * im.unit_cost) / NULLIF(SUM(im.quantity_change), 0),
        0
    ) AS avg_unit_cost  -- weighted average cost
FROM inventory_items ii
LEFT JOIN inventory_movements im ON im.inventory_item_id = ii.id
LEFT JOIN journal_entries je ON je.id = im.journal_entry_id
LEFT JOIN transactions t ON t.id = je.transaction_id AND t.is_posted = true
GROUP BY ii.tenant_id, ii.id, ii.name, ii.sku, ii.unit_type;

-- Currency exposure: what we hold in each currency
CREATE VIEW currency_exposure AS
SELECT
    je.tenant_id,
    je.currency_code,
    COALESCE(SUM(je.debit_amount), 0)  AS total_debits,
    COALESCE(SUM(je.credit_amount), 0) AS total_credits,
    COALESCE(SUM(
        CASE WHEN je.debit_amount > 0 THEN je.debit_amount ELSE -je.credit_amount END
    ), 0) AS net_position
FROM journal_entries je
JOIN transactions t ON t.id = je.transaction_id AND t.is_posted = true
GROUP BY je.tenant_id, je.currency_code;

-- =====================================================
-- FINANCIAL STATEMENTS VIEWS
-- =====================================================

-- Income Statement (Profit & Loss): Revenue - Expenses for a period
-- Supports date_from and date_to filtering
CREATE VIEW income_statement AS
SELECT
    je.tenant_id,
    a.type AS account_type,
    a.code AS account_code,
    a.name AS account_name,
    COALESCE(SUM(je.debit_amount), 0) AS total_debits,
    COALESCE(SUM(je.credit_amount), 0) AS total_credits,
    CASE a.type
        WHEN 'income' THEN COALESCE(SUM(je.credit_amount), 0) - COALESCE(SUM(je.debit_amount), 0)
        WHEN 'expense' THEN COALESCE(SUM(je.debit_amount), 0) - COALESCE(SUM(je.credit_amount), 0)
        ELSE 0
    END AS net_amount
FROM journal_entries je
JOIN transactions t ON t.id = je.transaction_id AND t.is_posted = true
JOIN accounts a ON a.id = je.account_id
WHERE a.type IN ('income', 'expense')
GROUP BY je.tenant_id, a.type, a.code, a.name;

-- Balance Sheet: Assets = Liabilities + Equity at a point in time
-- For any date, shows balances as of that date
CREATE VIEW balance_sheet AS
SELECT
    je.tenant_id,
    a.type AS account_type,
    a.code AS account_code,
    a.name AS account_name,
    a.normal_balance,
    CASE a.normal_balance
        WHEN 'debit' THEN COALESCE(SUM(je.debit_amount), 0) - COALESCE(SUM(je.credit_amount), 0)
        WHEN 'credit' THEN COALESCE(SUM(je.credit_amount), 0) - COALESCE(SUM(je.debit_amount), 0)
    END AS balance
FROM journal_entries je
JOIN transactions t ON t.id = je.transaction_id AND t.is_posted = true
JOIN accounts a ON a.id = je.account_id
WHERE a.type IN ('asset', 'liability', 'equity')
GROUP BY je.tenant_id, a.type, a.code, a.name, a.normal_balance;

-- Cash Flow Statement: Cash movements categorized
-- Operating: All regular business transactions through cash/bank accounts
-- Investing: Asset purchases/sales
-- Financing: Loans, owner capital
CREATE VIEW cash_flow_statement AS
SELECT
    je.tenant_id,
    t.date,
    a.type AS account_type,
    a.code AS account_code,
    a.name AS account_name,
    COALESCE(SUM(je.debit_amount), 0) AS total_debits,
    COALESCE(SUM(je.credit_amount), 0) AS total_credits,
    CASE
        WHEN a.type = 'asset' AND a.code IN ('1000', '1010', '1020', '1030', '1040', '1050') THEN 'cash_equivalent'
        WHEN a.type = 'income' AND a.code NOT IN ('4100') THEN 'operating'
        WHEN a.type = 'expense' AND a.code NOT IN ('5000') THEN 'operating'
        WHEN a.code = '5000' THEN 'cogs'
        WHEN a.code = '4100' THEN 'forex'
        ELSE 'other'
    END AS flow_category
FROM journal_entries je
JOIN transactions t ON t.id = je.transaction_id AND t.is_posted = true
JOIN accounts a ON a.id = je.account_id
GROUP BY je.tenant_id, t.date, a.type, a.code, a.name;

-- =====================================================
-- SEED: DEFAULT TENANT + CHART OF ACCOUNTS
-- Run once to bootstrap the system
-- =====================================================

-- Default tenant (replace with your actual name)
INSERT INTO tenants (id, name, base_currency) VALUES
('00000000-0000-0000-0000-000000000001', 'My Business', 'KES');

-- Standard Chart of Accounts
INSERT INTO accounts (tenant_id, code, name, type, normal_balance) VALUES
-- ASSETS
('00000000-0000-0000-0000-000000000001', '1000', 'Cash - Physical KES',   'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1010', 'Cash - USD',             'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1020', 'Cash - GBP',             'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1030', 'M-PESA',                 'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1040', 'Bank - KES',             'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1050', 'Bank - USD',             'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1100', 'Accounts Receivable',    'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1200', 'Inventory - General',    'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1210', 'Inventory - Phones',     'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1220', 'Inventory - Gold',       'asset', 'debit'),
('00000000-0000-0000-0000-000000000001', '1230', 'Inventory - Coffee',     'asset', 'debit'),
-- LIABILITIES
('00000000-0000-0000-0000-000000000001', '2000', 'Accounts Payable',       'liability', 'credit'),
('00000000-0000-0000-0000-000000000001', '2100', 'Loans Payable',          'liability', 'credit'),
-- EQUITY
('00000000-0000-0000-0000-000000000001', '3000', 'Owner Capital',          'equity', 'credit'),
('00000000-0000-0000-0000-000000000001', '3100', 'Retained Earnings',      'equity', 'credit'),
-- INCOME
('00000000-0000-0000-0000-000000000001', '4000', 'Sales Revenue',          'income', 'credit'),
('00000000-0000-0000-0000-000000000001', '4100', 'Forex Trading Gain',     'income', 'credit'),
('00000000-0000-0000-0000-000000000001', '4200', 'Commission Income',      'income', 'credit'),
-- EXPENSES
('00000000-0000-0000-0000-000000000001', '5000', 'Cost of Goods Sold',     'expense', 'debit'),
('00000000-0000-0000-0000-000000000001', '5100', 'Freight & Shipping',     'expense', 'debit'),
('00000000-0000-0000-0000-000000000001', '5200', 'Bank Charges',           'expense', 'debit'),
('00000000-0000-0000-0000-000000000001', '5300', 'Operating Expenses',     'expense', 'debit');
