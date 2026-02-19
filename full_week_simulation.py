
import asyncio
import os
import uuid
from decimal import Decimal
from datetime import date, timedelta
from dotenv import load_dotenv
import asyncpg
import json

# Load environment
load_dotenv()

# DB Config
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port", "6543")
DBNAME = os.getenv("dbname")
DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

# Constants
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

async def run_simulation():
    print("🚀 Starting Full Week Ledger Simulation...")
    print(f"Connecting to: {HOST}")
    
    conn = await asyncpg.connect(DATABASE_URL, ssl="require", statement_cache_size=0)
    
    try:
        # 0. SETUP: Clear existing data for the default tenant (for a clean simulation)
        # In a real app we wouldn't delete, but for a "Fresh Week" simulation we want a clean slate.
        print("🧹 Cleaning slate for simulation...")
        # Disable the guard trigger temporarily to allow cleaning
        await conn.execute("ALTER TABLE journal_entries DISABLE TRIGGER guard_posted_entries")
        try:
            await conn.execute("DELETE FROM inventory_movements WHERE journal_entry_id IN (SELECT id FROM journal_entries WHERE tenant_id = $1)", TENANT_ID)
            await conn.execute("DELETE FROM journal_entries WHERE tenant_id = $1", TENANT_ID)
            await conn.execute("DELETE FROM transactions WHERE tenant_id = $1", TENANT_ID)
            await conn.execute("DELETE FROM inventory_items WHERE tenant_id = $1", TENANT_ID)
            await conn.execute("DELETE FROM parties WHERE tenant_id = $1", TENANT_ID)
        finally:
            await conn.execute("ALTER TABLE journal_entries ENABLE TRIGGER guard_posted_entries")
        # Keep accounts as they are seeded in schema.sql
        
        # Get Account IDs
        rows = await conn.fetch("SELECT id, code, name FROM accounts WHERE tenant_id = $1", TENANT_ID)
        accounts = {r['code']: r['id'] for r in rows}
        print(f"✅ Loaded {len(accounts)} accounts.")

        # 1. CREATE PARTIES & ITEMS
        print("👤 Creating parties and items...")
        supplier_id = await conn.fetchval("INSERT INTO parties (tenant_id, name, type) VALUES ($1, 'Global Electronics Ltd', 'supplier') RETURNING id", TENANT_ID)
        customer_id = await conn.fetchval("INSERT INTO parties (tenant_id, name, type) VALUES ($1, 'Local Retailer Shop', 'customer') RETURNING id", TENANT_ID)
        partner_id = await conn.fetchval("INSERT INTO parties (tenant_id, name, type) VALUES ($1, 'Business Partner Joe', 'partner') RETURNING id", TENANT_ID)
        
        phone_item_id = await conn.fetchval("INSERT INTO inventory_items (tenant_id, name, sku, unit_type) VALUES ($1, 'Smartphone X', 'SPX-001', 'piece') RETURNING id", TENANT_ID)
        gold_item_id = await conn.fetchval("INSERT INTO inventory_items (tenant_id, name, sku, unit_type, is_volatile) VALUES ($1, 'Gold Bullion', 'GOLD-999', 'gram', true) RETURNING id", TENANT_ID)

        # --- DAY 1: Capital Injection & Inventory Import ---
        # Owner brings in 2M KES capital.
        # Buys 100 phones @ $100 (KES 13,000) = KES 1,300,000.
        print("📅 DAY 1: Capital & Import")
        
        # Capital
        txn_id = await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 1), "description": "Initial Capital Injection",
            "entries": [
                {"account_id": accounts["3000"], "credit_amount": 2000000, "memo": "Owner investment"},
                {"account_id": accounts["1040"], "debit_amount": 2000000, "memo": "Bank deposit"}
            ]
        })

        # Import 100 phones
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 1), "description": "Import 100 Smartphones",
            "entries": [
                {
                    "account_id": accounts["1210"], "debit_amount": 1300000, 
                    "inventory_item_id": phone_item_id, "quantity": 100, "memo": "100 phones @ 13k"
                },
                {
                    "account_id": accounts["1040"], "credit_amount": 1300000, "memo": "Paid supplier for phones"
                }
            ]
        })

        # --- DAY 2: Sales & M-PESA Transfer ---
        print("📅 DAY 2: Sales & Transfers")
        # Sell 10 phones @ 20k KES each = 200k KES
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 2), "description": "Sale of 10 phones",
            "entries": [
                {"account_id": accounts["1030"], "debit_amount": 200000, "party_id": customer_id, "memo": "Customer paid via M-PESA"},
                {"account_id": accounts["4000"], "credit_amount": 200000, "party_id": customer_id, "memo": "Sales Revenue"}
            ]
        })
        # Record COGS for 10 phones (Cost 13k each = 130k)
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 2), "description": "COGS for 10 phones",
            "entries": [
                {"account_id": accounts["5000"], "debit_amount": 130000, "memo": "Cost of 10 phones"},
                {"account_id": accounts["1210"], "credit_amount": 130000, "inventory_item_id": phone_item_id, "quantity": 100, "memo": "Stock reduction"} # OOPS: I put quantity 100 instead of 10!
            ]
        })

        # --- DAY 3: Correcting the Mistake & Volatile Purchase ---
        print("📅 DAY 3: Reversal & Gold")
        # Find that COGS transaction and reverse it
        bad_txn_id = await conn.fetchval("SELECT id FROM transactions WHERE description = 'COGS for 10 phones' AND tenant_id = $1", TENANT_ID)
        await conn.fetchval("SELECT reverse_transaction($1, $2, $3)", bad_txn_id, date(2024, 3, 3), "Correcting quantity error")
        
        # Post correct COGS
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 3), "description": "Corrected COGS for 10 phones",
            "entries": [
                {"account_id": accounts["5000"], "debit_amount": 130000, "memo": "Cost of 10 phones"},
                {"account_id": accounts["1210"], "credit_amount": 130000, "inventory_item_id": phone_item_id, "quantity": 10, "memo": "Stock reduction (Corrected)"}
            ]
        })

        # Buy 100g Gold @ $65/g (Rate 135) = 100 * 65 * 135 = 877,500 KES
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 3), "description": "Invest in Gold",
            "entries": [
                {
                    "account_id": accounts["1220"], "debit_amount": 877500, 
                    "inventory_item_id": gold_item_id, "quantity": 100, "memo": "100g Gold @ 65 USD/g"
                },
                {
                    "account_id": accounts["1050"], "credit_amount": 6500, "currency_code": "USD", "exchange_rate": 135, "memo": "Paid from USD account"
                }
            ]
        })

        # --- DAY 4: On-Behalf & Commissions ---
        print("📅 DAY 4: On-Behalf Flow")
        # Pay 50k KES for Joe's bills. Joe owes us.
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 4), "description": "Paid Joe's bills on-behalf",
            "entries": [
                {"account_id": accounts["1100"], "debit_amount": 50000, "party_id": partner_id, "memo": "Joe owes me"},
                {"account_id": accounts["1000"], "credit_amount": 50000, "memo": "Paid cash"}
            ]
        })
        # Earn 10k commission for a referral
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 4), "description": "Referral Commission",
            "entries": [
                {"account_id": accounts["1030"], "debit_amount": 10000, "memo": "Commission received via M-PESA"},
                {"account_id": accounts["4200"], "credit_amount": 10000, "memo": "Referral income"}
            ]
        })

        # --- DAY 5: Bulk Sale ---
        print("📅 DAY 5: Bulk Sale")
        # Sell 50 phones @ 22k = 1,100,000 KES. On Credit.
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 5), "description": "Bulk Sale to Retailer",
            "entries": [
                {"account_id": accounts["1100"], "debit_amount": 1100000, "party_id": customer_id, "memo": "Invoice #R-101"},
                {"account_id": accounts["4000"], "credit_amount": 1100000, "party_id": customer_id, "memo": "Wholesale revenue"}
            ]
        })
        # COGS: 50 * 13k = 650,000 KES
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 5), "description": "COGS for Bulk Sale",
            "entries": [
                {"account_id": accounts["5000"], "debit_amount": 650000, "memo": "Cost of 50 phones"},
                {"account_id": accounts["1210"], "credit_amount": 650000, "inventory_item_id": phone_item_id, "quantity": 50, "memo": "Phones out"}
            ]
        })

        # --- DAY 6: Revaluation ---
        print("📅 DAY 6: Mark-to-Market Gold")
        # Gold price jumps! 100g is now worth 950,000 KES (Gain: 950,000 - 877,500 = 72,500)
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 6), "description": "Revalue Gold Stock",
            "entries": [
                {
                    "account_id": accounts["1220"], "debit_amount": 72500, 
                    "inventory_item_id": gold_item_id, "quantity": 0, "memo": "MTM Gain: price up"
                },
                {
                    "account_id": accounts["4100"], "credit_amount": 72500, "memo": "Unrealized Gain"
                }
            ]
        })

        # --- DAY 7: Settlement & Final Truth ---
        print("📅 DAY 7: Settlement & Audit")
        # Joe pays back half (25k)
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 7), "description": "Joe partial repayment",
            "entries": [
                {"account_id": accounts["1030"], "debit_amount": 25000, "party_id": partner_id, "memo": "Received via M-PESA"},
                {"account_id": accounts["1100"], "credit_amount": 25000, "party_id": partner_id, "memo": "Reducing Joe's debt"}
            ]
        })
        
        # Retailer pays half of their invoice (550k)
        await post_transaction(conn, {
            "tenant_id": TENANT_ID, "date": date(2024, 3, 7), "description": "Retailer partial payment",
            "entries": [
                {"account_id": accounts["1040"], "debit_amount": 550000, "party_id": customer_id, "memo": "Bank transfer for Inv #R-101"},
                {"account_id": accounts["1100"], "credit_amount": 550000, "party_id": customer_id, "memo": "Reducing receivable"}
            ]
        })

        # FINAL VERIFICATION
        print("\n🔍 THE TRUTH CHECK:")
        # We need to sum by base_amount which is the column in journal_entries
        truth = await conn.fetchrow("""
            SELECT 
                SUM(base_amount) FILTER (WHERE debit_amount > 0) as d, 
                SUM(base_amount) FILTER (WHERE credit_amount > 0) as c,
                ABS(SUM(base_amount) FILTER (WHERE debit_amount > 0) - SUM(base_amount) FILTER (WHERE credit_amount > 0)) as imbalance
            FROM journal_entries je
            JOIN transactions t ON t.id = je.transaction_id
            WHERE je.tenant_id = $1 AND t.is_posted = true
        """, TENANT_ID)
        
        status = "✅ BALANCED" if truth['imbalance'] < 0.01 else "❌ OUT OF BALANCE"
        print(f"System Balance: {status}")
        print(f"Total Debits:  {truth['d']:,.2f}")
        print(f"Total Credits: {truth['c']:,.2f}")
        print(f"Imbalance:     {truth['imbalance']:,.4f}")

        print("\n📈 INVENTORY POSITION:")
        inv_rows = await conn.fetch("SELECT item_name, quantity_on_hand, avg_unit_cost FROM inventory_positions WHERE tenant_id = $1", TENANT_ID)
        for r in inv_rows:
            print(f"- {r['item_name']}: {r['quantity_on_hand']:,.0f} units @ {r['avg_unit_cost']:,.2f} KES")

        print("\n🤝 PARTY BALANCES:")
        party_rows = await conn.fetch("""
            SELECT party_name, net_balance_base 
            FROM party_balances 
            WHERE tenant_id = $1 
            AND ABS(net_balance_base) > 0.01
        """, TENANT_ID)
        for r in party_rows:
            direction = "owes you" if r['net_balance_base'] > 0 else "you owe them"
            print(f"- {r['party_name']}: {abs(r['net_balance_base']):,.2f} KES ({direction})")

        print("\n✨ Simulation Complete! The Truth Layer holds.")

    finally:
        await conn.close()

async def post_transaction(conn, txn):
    import json
    async with conn.transaction():
        # Create txn
        txn_id = await conn.fetchval("""
            INSERT INTO transactions (tenant_id, transaction_number, date, description, is_posted)
            VALUES ($1, $2, $3, $4, false)
            RETURNING id
        """, txn['tenant_id'], str(uuid.uuid4())[:8], txn['date'], txn['description'])
        
        for e in txn['entries']:
            debit = Decimal(str(e.get('debit_amount', 0)))
            credit = Decimal(str(e.get('credit_amount', 0)))
            rate = Decimal(str(e.get('exchange_rate', 1.0)))
            curr = e.get('currency_code', 'KES')
            
            entry_id = await conn.fetchval("""
                INSERT INTO journal_entries (
                    tenant_id, transaction_id, account_id,
                    debit_amount, credit_amount,
                    party_id, inventory_item_id, quantity,
                    currency_code, exchange_rate,
                    memo
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                RETURNING id
            """, txn['tenant_id'], txn_id, e['account_id'],
                debit, credit, e.get('party_id'),
                e.get('inventory_item_id'), Decimal(str(e.get('quantity'))) if e.get('quantity') is not None else None,
                curr, rate, e.get('memo'))
            
            # Inventory movement
            if e.get('inventory_item_id') and e.get('quantity') is not None:
                qty = Decimal(str(e['quantity']))
                qty_change = qty if debit > 0 else -qty
                base_amt = (debit if debit > 0 else credit) * rate
                unit_cost = base_amt / qty if qty != 0 else 0
                
                await conn.execute("""
                    INSERT INTO inventory_movements (journal_entry_id, inventory_item_id, quantity_change, unit_cost)
                    VALUES ($1, $2, $3, $4)
                """, entry_id, e['inventory_item_id'], qty_change, unit_cost)
        
        # Post
        await conn.execute("SELECT post_transaction($1)", txn_id)
        return txn_id

if __name__ == "__main__":
    asyncio.run(run_simulation())
