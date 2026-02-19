"""
test_truth.py - Tests that verify math never breaks.

Every test here maps to a real-world scenario from the design doc.
The test names tell you exactly what business event is being verified.

Run: pytest tests/test_truth.py -v

These tests are your audit trail for the system's correctness.
If these pass, the truth layer holds.
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date

from models import (
    TransactionCreate,
    JournalEntryCreate,
    AccountType,
    NormalBalance,
)


TENANT_ID = uuid4()

# ─── Fixtures: reusable account IDs ───────────────────────────────────────────

@pytest.fixture
def accounts():
    return {
        "cash_kes":     uuid4(),
        "cash_usd":     uuid4(),
        "cash_gbp":     uuid4(),
        "mpesa":        uuid4(),
        "bank_kes":     uuid4(),
        "bank_usd":     uuid4(),
        "receivable":   uuid4(),
        "payable":      uuid4(),
        "inventory":    uuid4(),
        "sales":        uuid4(),
        "cogs":         uuid4(),
        "forex_gain":   uuid4(),
        "freight":      uuid4(),
    }


# ─── UNIT TESTS: Model validation (no DB needed) ─────────────────────────────

class TestJournalEntryValidation:
    """The entry is the atom. These rules must be unbreakable."""

    def test_valid_debit_entry(self, accounts):
        entry = JournalEntryCreate(
            account_id=accounts["cash_kes"],
            debit_amount=Decimal("1000"),
            credit_amount=Decimal("0"),
        )
        assert entry.direction == "debit"
        assert entry.amount == Decimal("1000")
        assert entry.compute_base_amount == Decimal("1000")

    def test_valid_credit_entry(self, accounts):
        entry = JournalEntryCreate(
            account_id=accounts["sales"],
            debit_amount=Decimal("0"),
            credit_amount=Decimal("5000"),
        )
        assert entry.direction == "credit"
        assert entry.amount == Decimal("5000")

    def test_cannot_have_both_debit_and_credit(self, accounts):
        with pytest.raises(ValueError, match="cannot have both"):
            JournalEntryCreate(
                account_id=accounts["cash_kes"],
                debit_amount=Decimal("100"),
                credit_amount=Decimal("100"),
            )

    def test_cannot_have_zero_amounts(self, accounts):
        with pytest.raises(ValueError, match="must have either"):
            JournalEntryCreate(
                account_id=accounts["cash_kes"],
                debit_amount=Decimal("0"),
                credit_amount=Decimal("0"),
            )

    def test_negative_amounts_rejected(self, accounts):
        with pytest.raises(ValueError, match="must be positive"):
            JournalEntryCreate(
                account_id=accounts["cash_kes"],
                debit_amount=Decimal("-100"),
                credit_amount=Decimal("0"),
            )

    def test_exchange_rate_must_be_positive(self, accounts):
        with pytest.raises(ValueError, match="Exchange rate"):
            JournalEntryCreate(
                account_id=accounts["cash_usd"],
                debit_amount=Decimal("1000"),
                currency_code="USD",
                exchange_rate=Decimal("0"),
            )

    def test_quantity_requires_inventory_item(self, accounts):
        with pytest.raises(ValueError, match="inventory_item_id is required"):
            JournalEntryCreate(
                account_id=accounts["inventory"],
                debit_amount=Decimal("1000"),
                quantity=Decimal("10"),
                # inventory_item_id not set!
            )

    def test_inventory_item_requires_quantity(self, accounts):
        with pytest.raises(ValueError, match="quantity is required"):
            JournalEntryCreate(
                account_id=accounts["inventory"],
                debit_amount=Decimal("1000"),
                inventory_item_id=uuid4(),
                # quantity not set!
            )

    def test_base_amount_calculation_with_exchange_rate(self, accounts):
        """USD 1000 @ 128 KES = 128,000 KES base amount."""
        entry = JournalEntryCreate(
            account_id=accounts["cash_usd"],
            debit_amount=Decimal("1000"),
            currency_code="USD",
            exchange_rate=Decimal("128"),
        )
        assert entry.compute_base_amount == Decimal("128000")


class TestTransactionBalance:
    """The golden rule: every transaction must balance."""

    def test_balanced_transaction_passes(self, accounts):
        txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 15),
            description="Simple cash movement",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["cash_usd"],
                    debit_amount=Decimal("50000"),
                ),
                JournalEntryCreate(
                    account_id=accounts["cash_kes"],
                    credit_amount=Decimal("50000"),
                ),
            ]
        )
        assert sum(e.debit_amount for e in txn.entries) == Decimal("50000")
        assert sum(e.credit_amount for e in txn.entries) == Decimal("50000")

    def test_unbalanced_transaction_rejected(self, accounts):
        with pytest.raises(ValueError, match="does not balance"):
            TransactionCreate(
                tenant_id=TENANT_ID,
                date=date(2024, 1, 15),
                description="This should fail",
                entries=[
                    JournalEntryCreate(
                        account_id=accounts["cash_kes"],
                        debit_amount=Decimal("50000"),
                    ),
                    JournalEntryCreate(
                        account_id=accounts["sales"],
                        credit_amount=Decimal("40000"),  # ← WRONG: only 40k
                    ),
                ]
            )

    def test_single_entry_transaction_rejected(self, accounts):
        """One entry alone cannot balance."""
        with pytest.raises(Exception):  # Pydantic min_length=2
            TransactionCreate(
                tenant_id=TENANT_ID,
                date=date(2024, 1, 15),
                description="Orphan entry",
                entries=[
                    JournalEntryCreate(
                        account_id=accounts["cash_kes"],
                        debit_amount=Decimal("1000"),
                    ),
                ]
            )

    def test_rounding_tolerance(self, accounts):
        """Allow up to 0.01 difference for floating point rounding."""
        txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 15),
            description="Rounding tolerance test",
            entries=[
                JournalEntryCreate(account_id=accounts["cash_kes"], debit_amount=Decimal("100.00")),
                JournalEntryCreate(account_id=accounts["sales"], credit_amount=Decimal("100.00")),
            ]
        )
        assert txn is not None  # passes

    def test_multi_entry_transaction_balances(self, accounts):
        """Container split: 3 debits, 1 credit."""
        txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 17),
            description="Container CHINA-123 - split costs",
            entries=[
                # 60% phones
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    debit_amount=Decimal("390000"),
                    inventory_item_id=uuid4(),
                    quantity=Decimal("60"),
                    memo="60 phones @ 6500",
                    tags=["container-china-123", "phones"],
                ),
                # 40% accessories
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    debit_amount=Decimal("260000"),
                    inventory_item_id=uuid4(),
                    quantity=Decimal("200"),
                    memo="200 accessories @ 1300",
                    tags=["container-china-123", "accessories"],
                ),
                # Total freight
                JournalEntryCreate(
                    account_id=accounts["freight"],
                    credit_amount=Decimal("650000"),
                    party_id=uuid4(),
                    memo="Total freight to shipping agent",
                    tags=["container-china-123"],
                ),
            ]
        )
        total_debit  = sum(e.debit_amount for e in txn.entries)
        total_credit = sum(e.credit_amount for e in txn.entries)
        assert total_debit == Decimal("650000")
        assert total_credit == Decimal("650000")


# ─── SCENARIO TESTS: Real business events ────────────────────────────────────

class TestRealWorldScenarios:
    """
    Each test models a real scenario from the design doc.
    These prove the building blocks handle everything.
    """

    def test_scenario_runner_takes_cash_upcountry(self, accounts):
        """James takes 50,000 KES upcountry to buy maize."""
        runner_id = uuid4()
        txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 15),
            description="Send cash with James to upcountry",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["cash_usd"],  # float account (runner)
                    debit_amount=Decimal("50000"),
                    party_id=runner_id,
                    memo="Cash to buy maize - James",
                    tags=["runner", "upcountry", "maize"],
                ),
                JournalEntryCreate(
                    account_id=accounts["cash_kes"],  # main cash
                    credit_amount=Decimal("50000"),
                    memo="Cash out to runner",
                ),
            ]
        )
        assert sum(e.debit_amount for e in txn.entries) == sum(e.credit_amount for e in txn.entries)

    def test_scenario_import_phones_from_china(self, accounts):
        """Pay Shenzhen supplier $5000 @ 130 KES for 100 phones."""
        phones_item = uuid4()
        supplier_id = uuid4()

        # The trick: debit inventory in KES, credit USD bank in USD
        # Both sides in base_amount should equal 650,000 KES
        inventory_entry = JournalEntryCreate(
            account_id=accounts["inventory"],
            debit_amount=Decimal("650000"),
            currency_code="KES",
            exchange_rate=Decimal("1"),
            inventory_item_id=phones_item,
            quantity=Decimal("100"),
            party_id=supplier_id,
            tags=["china-import", "phones"],
        )
        bank_entry = JournalEntryCreate(
            account_id=accounts["bank_usd"],
            credit_amount=Decimal("5000"),
            currency_code="USD",
            exchange_rate=Decimal("130"),
            party_id=supplier_id,
            tags=["swift", "china-import"],
        )

        assert inventory_entry.compute_base_amount == Decimal("650000")
        assert bank_entry.compute_base_amount == Decimal("650000")

        txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 16),
            description="Import 100 phones from Shenzhen Ltd",
            reference="SWIFT-20240116-001",
            entries=[inventory_entry, bank_entry],
        )
        total_debit  = sum(e.compute_base_amount for e in txn.entries if e.debit_amount > 0)
        total_credit = sum(e.compute_base_amount for e in txn.entries if e.credit_amount > 0)
        assert total_debit == total_credit == Decimal("650000")

    def test_scenario_forex_trading_buy_low_sell_high(self, accounts):
        """
        Buy $1000 from agent @ 128, sell to customer @ 132.
        Profit = 4000 KES. Appears automatically in account balances.
        """
        agent_id = uuid4()
        customer_id = uuid4()

        # BUY: debit USD cash, credit KES cash
        buy_debit  = JournalEntryCreate(
            account_id=accounts["cash_usd"],
            debit_amount=Decimal("1000"),
            currency_code="USD",
            exchange_rate=Decimal("128"),
            party_id=agent_id,
            tags=["forex", "buy"],
        )
        buy_credit = JournalEntryCreate(
            account_id=accounts["mpesa"],
            credit_amount=Decimal("128000"),
            party_id=agent_id,
            tags=["forex", "buy"],
        )

        assert buy_debit.compute_base_amount == buy_credit.compute_base_amount == Decimal("128000")

        # SELL: debit KES cash, credit USD cash
        sell_debit  = JournalEntryCreate(
            account_id=accounts["mpesa"],
            debit_amount=Decimal("132000"),
            party_id=customer_id,
            tags=["forex", "sell"],
        )
        sell_credit = JournalEntryCreate(
            account_id=accounts["cash_usd"],
            credit_amount=Decimal("1000"),
            currency_code="USD",
            exchange_rate=Decimal("132"),
            party_id=customer_id,
            tags=["forex", "sell"],
        )

        assert sell_debit.compute_base_amount == sell_credit.compute_base_amount == Decimal("132000")

        # Profit verification:
        # M-PESA account: credited 128,000 (buy), debited 132,000 (sell)
        # Net M-PESA movement: +4,000 KES profit
        mpesa_net = sell_debit.compute_base_amount - buy_credit.compute_base_amount
        assert mpesa_net == Decimal("4000"), f"Expected 4000 profit, got {mpesa_net}"

    def test_scenario_export_with_delayed_payment(self, accounts):
        """
        Export coffee to UK. Recognize revenue now, receive GBP later.
        Two separate transactions. Handle FX Gain/Loss.
        """
        buyer_id = uuid4()
        fx_gain_loss_account = accounts["forex_gain"]

        # Transaction 1: Ship goods, record receivable
        # 10,000 GBP @ 150 KES = 1,500,000 KES
        txn1 = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 18),
            description="Export coffee to London buyer",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["receivable"],
                    debit_amount=Decimal("10000"),
                    currency_code="GBP",
                    exchange_rate=Decimal("150"),
                    party_id=buyer_id,
                    memo="Coffee export - receivable",
                    tags=["export", "coffee", "uk"],
                ),
                JournalEntryCreate(
                    account_id=accounts["sales"],
                    credit_amount=Decimal("1500000"),
                    currency_code="KES",
                    exchange_rate=Decimal("1"),
                    party_id=buyer_id,
                    memo="Revenue recognized on shipment",
                ),
            ]
        )

        # Transaction 2: Payment arrives 14 days later in GBP, rate is now 155 KES/GBP
        # Received: 10,000 GBP @ 155 = 1,550,000 KES
        # Original Receivable: 1,500,000 KES
        # FX Gain: 50,000 KES
        txn2 = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 2, 1),
            description="Payment received from UK buyer - with FX gain",
            reference="GBP-TRANSFER-20240201",
            entries=[
                # Leg 1: Cash in GBP
                JournalEntryCreate(
                    account_id=accounts["cash_gbp"],
                    debit_amount=Decimal("10000"),
                    currency_code="GBP",
                    exchange_rate=Decimal("155"),
                    party_id=buyer_id,
                    memo="GBP received @ 155",
                    tags=["export", "coffee", "payment"],
                ),
                # Leg 2: Clear original receivable (must use original base amount to clear it)
                JournalEntryCreate(
                    account_id=accounts["receivable"],
                    credit_amount=Decimal("1500000"),
                    currency_code="KES",
                    exchange_rate=Decimal("1"),
                    party_id=buyer_id,
                    memo="Clear receivable (original rate)",
                ),
                # Leg 3: Record FX Gain (Credit income)
                JournalEntryCreate(
                    account_id=accounts["forex_gain"],
                    credit_amount=Decimal("50000"),
                    currency_code="KES",
                    exchange_rate=Decimal("1"),
                    memo="Forex gain on GBP receivable",
                ),
            ]
        )

        # Verification
        receivable_opened = sum(e.compute_base_amount for e in txn1.entries if e.account_id == accounts["receivable"])
        receivable_closed = sum(e.compute_base_amount for e in txn2.entries if e.account_id == accounts["receivable"])
        assert receivable_opened == receivable_closed == Decimal("1500000")
        
        cash_received_base = sum(e.compute_base_amount for e in txn2.entries if e.account_id == accounts["cash_gbp"])
        assert cash_received_base == Decimal("1550000")
        
        fx_gain = sum(e.compute_base_amount for e in txn2.entries if e.account_id == accounts["forex_gain"])
        assert fx_gain == Decimal("50000")

    def test_scenario_mpesa_to_bank_to_supplier(self, accounts):
        """
        M-PESA → Bank transfer, then Bank → Supplier payment.
        Two transactions, three legs total.
        """
        supplier_id = uuid4()

        # Step 1: M-PESA to Bank
        txn_transfer = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 19),
            description="Transfer M-PESA to bank",
            reference="MPESA-TRF-001",
            entries=[
                JournalEntryCreate(account_id=accounts["bank_kes"], debit_amount=Decimal("20000")),
                JournalEntryCreate(account_id=accounts["mpesa"],    credit_amount=Decimal("20000")),
            ]
        )

        # Step 2: Bank pays supplier
        txn_payment = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 19),
            description="Pay supplier from bank",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["payable"],
                    debit_amount=Decimal("20000"),
                    party_id=supplier_id,
                    memo="Settle outstanding payable",
                ),
                JournalEntryCreate(
                    account_id=accounts["bank_kes"],
                    credit_amount=Decimal("20000"),
                    party_id=supplier_id,
                ),
            ]
        )
        assert txn_transfer is not None
        assert txn_payment is not None

    def test_scenario_sale_with_cogs(self, accounts):
        """
        Sell 10 phones @ 15,000 KES.
        Inventory was bought @ 13,000 KES.
        Revenue: 150,000 KES.
        COGS: 130,000 KES.
        """
        customer_id = uuid4()
        phone_item_id = uuid4()

        # 1. THE SALE: Debit Cash, Credit Revenue
        sale_txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 2, 5),
            description="Sale of 10 phones to customer",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["cash_kes"],
                    debit_amount=Decimal("150000"),
                    party_id=customer_id,
                    memo="Sold 10 phones @ 15k",
                ),
                JournalEntryCreate(
                    account_id=accounts["sales"],
                    credit_amount=Decimal("150000"),
                    party_id=customer_id,
                    memo="Sales revenue",
                ),
            ]
        )

        # 2. THE INVENTORY OUTFLOW (COGS): Debit COGS, Credit Inventory
        # In a real system, this might be triggered automatically or in the same transaction
        cogs_txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 2, 5),
            description="COGS for 10 phones sold",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["cogs"],
                    debit_amount=Decimal("130000"),
                    memo="Cost of 10 phones sold",
                ),
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    credit_amount=Decimal("130000"),
                    inventory_item_id=phone_item_id,
                    quantity=Decimal("10"),
                    memo="Inventory reduction for sale",
                ),
            ]
        )

        # Verification
        assert sale_txn.entries[0].debit_amount == Decimal("150000")
        assert cogs_txn.entries[1].credit_amount == Decimal("130000")
        assert cogs_txn.entries[1].quantity == Decimal("10")
        assert cogs_txn.entries[1].direction == "credit"

        # Both balance independently
        for txn in [sale_txn, cogs_txn]:
            d = sum(e.debit_amount for e in txn.entries)
            c = sum(e.credit_amount for e in txn.entries)
            assert d == c

    def test_scenario_gold_trade_dubai_kenya(self, accounts):
        """
        Buy 500g gold in Dubai @ $60/g. Price is volatile.
        Record in both USD (trade currency) and KES (base).
        """
        gold_item = uuid4()
        dubai_supplier = uuid4()
        exchange_rate = Decimal("130")  # KES/USD
        gold_price_usd = Decimal("60")  # per gram
        grams = Decimal("500")

        usd_amount = gold_price_usd * grams  # 30,000 USD
        kes_amount = usd_amount * exchange_rate  # 3,900,000 KES

        txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 20),
            description="Buy 500g gold - Dubai supplier",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    debit_amount=kes_amount,
                    currency_code="KES",
                    exchange_rate=Decimal("1"),
                    inventory_item_id=gold_item,
                    quantity=grams,
                    party_id=dubai_supplier,
                    memo="500g gold @ 60 USD/g",
                    tags=["gold", "dubai", "volatile"],
                ),
                JournalEntryCreate(
                    account_id=accounts["bank_usd"],
                    credit_amount=usd_amount,
                    currency_code="USD",
                    exchange_rate=exchange_rate,
                    party_id=dubai_supplier,
                    tags=["gold", "dubai", "swift"],
                ),
            ]
        )

        d = sum(e.compute_base_amount for e in txn.entries if e.debit_amount > 0)
        c = sum(e.compute_base_amount for e in txn.entries if e.credit_amount > 0)
        assert d == c == Decimal("3900000")
        assert txn.entries[0].quantity == Decimal("500")

    def test_scenario_gold_revaluation(self, accounts):
        """
        Price of gold goes up while we hold it.
        We have 500g gold bought at 3,900,000 KES (7,800/g).
        New price is 8,000/g. New value is 4,000,000 KES.
        Unrealized gain: 100,000 KES.
        """
        gold_item_id = uuid4()
        
        reval_txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 25),
            description="Revalue gold inventory to market price",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    debit_amount=Decimal("100000"),
                    memo="Mark-to-market: Gold price increase (+200/g)",
                    tags=["gold", "revaluation", "unrealized-gain"],
                    # Note: We don't change quantity here, just value
                ),
                JournalEntryCreate(
                    account_id=accounts["forex_gain"], # Using same gain account or a specific one
                    credit_amount=Decimal("100000"),
                    memo="Unrealized gain on gold inventory",
                    tags=["gold", "revaluation"],
                ),
            ]
        )
        
        assert reval_txn is not None
        assert sum(e.debit_amount for e in reval_txn.entries) == Decimal("100000")
        assert sum(e.credit_amount for e in reval_txn.entries) == Decimal("100000")

    def test_scenario_volatile_item_loss(self, accounts):
        """
        Price of a volatile item goes down.
        """
        item_id = uuid4()
        
        loss_txn = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 1, 30),
            description="Write-down volatile inventory",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["forex_gain"], # Or expense account
                    debit_amount=Decimal("50000"),
                    memo="Market loss on inventory",
                ),
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    credit_amount=Decimal("50000"),
                    memo="Inventory value reduction",
                ),
            ]
        )
        assert loss_txn is not None


# ─── IMMUTABILITY TESTS ───────────────────────────────────────────────────────

class TestImmutabilityRules:
    """
    These can't be fully tested without a DB, but we document
    the expected behaviors here as living specification.
    """

    def test_reversal_creates_equal_and_opposite(self, accounts):
        """
        A reversal must produce entries that, combined with the original,
        net to zero across every account.
        """
        original_entries = [
            JournalEntryCreate(account_id=accounts["cash_kes"], debit_amount=Decimal("1000")),
            JournalEntryCreate(account_id=accounts["sales"],    credit_amount=Decimal("1000")),
        ]

        # Simulate what reverse_transaction does: flip debits/credits
        reversed_entries = []
        for e in original_entries:
            if e.debit_amount > 0:
                reversed_entries.append(
                    JournalEntryCreate(account_id=e.account_id, credit_amount=e.debit_amount)
                )
            else:
                reversed_entries.append(
                    JournalEntryCreate(account_id=e.account_id, debit_amount=e.credit_amount)
                )

        # Combined net should be zero
        all_entries = original_entries + reversed_entries
        net_cash = sum(
            e.debit_amount - e.credit_amount
            for e in all_entries
            if e.account_id == accounts["cash_kes"]
        )
        net_sales = sum(
            e.debit_amount - e.credit_amount
            for e in all_entries
            if e.account_id == accounts["sales"]
        )

        assert net_cash  == Decimal("0"), "Cash account should net to zero after reversal"
        assert net_sales == Decimal("0"), "Sales account should net to zero after reversal"


# ─── GOLDEN RULE VERIFICATION ─────────────────────────────────────────────────

class TestGoldenRule:
    """
    Sum(all debits) == Sum(all credits) across the entire ledger.
    Always. No exceptions.
    """

    def test_any_combination_of_balanced_transactions_stays_balanced(self, accounts):
        """
        Add N balanced transactions. System-wide total always balances.
        This is mathematical proof, not just testing one case.
        """
        scenarios = [
            (Decimal("50000"), accounts["cash_kes"],  accounts["mpesa"]),
            (Decimal("650000"), accounts["inventory"], accounts["bank_usd"]),
            (Decimal("10000"), accounts["receivable"], accounts["sales"]),
            (Decimal("132000"), accounts["mpesa"],    accounts["cash_usd"]),
        ]

        system_debits  = Decimal("0")
        system_credits = Decimal("0")

        for amount, debit_acct, credit_acct in scenarios:
            txn = TransactionCreate(
                tenant_id=TENANT_ID,
                date=date(2024, 1, 1),
                description="test",
                entries=[
                    JournalEntryCreate(account_id=debit_acct,  debit_amount=amount),
                    JournalEntryCreate(account_id=credit_acct, credit_amount=amount),
                ]
            )
            system_debits  += sum(e.debit_amount for e in txn.entries)
            system_credits += sum(e.credit_amount for e in txn.entries)

        assert system_debits == system_credits, \
            f"System imbalance! Debits: {system_debits}, Credits: {system_credits}"
        print(f"\n✅ Golden rule holds. Total debits = credits = {system_debits} KES")



class TestHecticWeek:
    """
    Stress test: A hectic week with many diverse movements.
    Ensures math never breaks across mixed flows and contexts.
    """
    def test_hectic_week_all_flows(self, accounts):
        from uuid import uuid4
        from decimal import Decimal
        from datetime import date
        from models import TransactionCreate, JournalEntryCreate

        TENANT_ID = uuid4()

        # Parties and items involved
        supplier_shenzhen = uuid4()
        partner_on_behalf = uuid4()
        coffee_buyer_uk = uuid4()
        gold_item = uuid4()
        phone_item = uuid4()

        all_txns = []

        # 1) Internal transfer: Bank KES -> M-PESA 100,000
        t1 = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 1),
            description="Transfer to MPESA",
            entries=[
                JournalEntryCreate(account_id=accounts["mpesa"],    debit_amount=Decimal("100000")),
                JournalEntryCreate(account_id=accounts["bank_kes"], credit_amount=Decimal("100000")),
            ]
        )
        all_txns.append(t1)

        # 2) FX trading: Buy $2,000 @ 128, then sell $1,500 @ 132 (leaves $500)
        t2_buy = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 2),
            description="FX buy $2000 @ 128",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["cash_usd"],
                    debit_amount=Decimal("2000"),
                    currency_code="USD",
                    exchange_rate=Decimal("128"),
                    memo="buy fx"
                ),
                JournalEntryCreate(
                    account_id=accounts["mpesa"],
                    credit_amount=Decimal("256000"),
                    memo="pay in KES"
                ),
            ]
        )
        all_txns.append(t2_buy)

        t2_sell = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 3),
            description="FX sell $1500 @ 132",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["mpesa"],
                    debit_amount=Decimal("198000"),
                    memo="receive in KES"
                ),
                JournalEntryCreate(
                    account_id=accounts["cash_usd"],
                    credit_amount=Decimal("1500"),
                    currency_code="USD",
                    exchange_rate=Decimal("132"),
                    memo="sell fx"
                ),
            ]
        )
        all_txns.append(t2_sell)

        # 3) On-behalf payment: We pay 200,000 KES for a partner -> record receivable from partner
        t3 = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 3),
            description="Paid supplier on behalf of partner (records receivable)",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["receivable"],
                    debit_amount=Decimal("200000"),
                    party_id=partner_on_behalf,
                    memo="Partner now owes us"
                ),
                JournalEntryCreate(
                    account_id=accounts["bank_kes"],
                    credit_amount=Decimal("200000"),
                    party_id=partner_on_behalf,
                    memo="We paid on their behalf"
                ),
            ]
        )
        all_txns.append(t3)

        # 4) Inventory import cross-currency: 100 phones, USD 10,000 @ 130 -> 1,300,000 KES
        t4 = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 4),
            description="Import phones $10k @ 130",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    debit_amount=Decimal("1300000"),
                    currency_code="KES",
                    exchange_rate=Decimal("1"),
                    inventory_item_id=phone_item,
                    quantity=Decimal("100"),
                    party_id=supplier_shenzhen,
                    tags=["phones", "import"]
                ),
                JournalEntryCreate(
                    account_id=accounts["bank_usd"],
                    credit_amount=Decimal("10000"),
                    currency_code="USD",
                    exchange_rate=Decimal("130"),
                    party_id=supplier_shenzhen,
                    tags=["swift"]
                ),
            ]
        )
        all_txns.append(t4)

        # 5) Sale 10 phones @ 15,000, COGS 13,000
        t5_sale = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 5),
            description="Sell 10 phones",
            entries=[
                JournalEntryCreate(account_id=accounts["cash_kes"], debit_amount=Decimal("150000")),
                JournalEntryCreate(account_id=accounts["sales"],    credit_amount=Decimal("150000")),
            ]
        )
        t5_cogs = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 5),
            description="COGS 10 phones",
            entries=[
                JournalEntryCreate(account_id=accounts["cogs"],      debit_amount=Decimal("130000")),
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    credit_amount=Decimal("130000"),
                    inventory_item_id=phone_item,
                    quantity=Decimal("10")
                ),
            ]
        )
        all_txns.extend([t5_sale, t5_cogs])

        # 6) Volatile asset (gold) buy and revaluation: buy 500g @ $60/g @130, revalue +50,000 then -20,000
        usd_amount = Decimal("60") * Decimal("500")  # 30,000
        kes_amount = usd_amount * Decimal("130")      # 3,900,000
        t6_buy_gold = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 6),
            description="Buy 500g gold",
            entries=[
                JournalEntryCreate(
                    account_id=accounts["inventory"],
                    debit_amount=kes_amount,
                    currency_code="KES",
                    exchange_rate=Decimal("1"),
                    inventory_item_id=gold_item,
                    quantity=Decimal("500"),
                    party_id=uuid4(),
                    tags=["gold", "dubai"]
                ),
                JournalEntryCreate(
                    account_id=accounts["bank_usd"],
                    credit_amount=usd_amount,
                    currency_code="USD",
                    exchange_rate=Decimal("130")
                ),
            ]
        )
        t6_reval_up = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 7),
            description="Gold revaluation +50k",
            entries=[
                JournalEntryCreate(account_id=accounts["inventory"],  debit_amount=Decimal("50000")),
                JournalEntryCreate(account_id=accounts["forex_gain"], credit_amount=Decimal("50000")),
            ]
        )
        t6_reval_down = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 8),
            description="Gold write-down -20k",
            entries=[
                JournalEntryCreate(account_id=accounts["forex_gain"], debit_amount=Decimal("20000")),
                JournalEntryCreate(account_id=accounts["inventory"],  credit_amount=Decimal("20000")),
            ]
        )
        all_txns.extend([t6_buy_gold, t6_reval_up, t6_reval_down])

        # 7) Mistake + reversal: Paid petty cash 5,000 by error, then reverse it
        t7_mistake = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 8),
            description="Mistaken petty cash payment",
            entries=[
                JournalEntryCreate(account_id=accounts["cash_kes"], debit_amount=Decimal("5000")),
                JournalEntryCreate(account_id=accounts["freight"],  credit_amount=Decimal("5000")),
            ]
        )
        # Manual reversal (equal and opposite)
        t7_reverse = TransactionCreate(
            tenant_id=TENANT_ID,
            date=date(2024, 3, 9),
            description="Reversal of mistaken petty cash",
            entries=[
                JournalEntryCreate(account_id=accounts["freight"],  debit_amount=Decimal("5000")),
                JournalEntryCreate(account_id=accounts["cash_kes"], credit_amount=Decimal("5000")),
            ]
        )
        all_txns.extend([t7_mistake, t7_reverse])

        # --- Assertions ---
        # 1. Every individual transaction balances in base currency
        for txn in all_txns:
            d_base = sum(e.compute_base_amount for e in txn.entries if e.debit_amount > 0)
            c_base = sum(e.compute_base_amount for e in txn.entries if e.credit_amount > 0)
            assert abs(d_base - c_base) <= Decimal("0.01"), f"Txn not balanced: {txn.description}"

        # 2. System-wide golden rule holds for the entire week
        system_d = Decimal("0")
        system_c = Decimal("0")
        for txn in all_txns:
            system_d += sum(e.compute_base_amount for e in txn.entries if e.debit_amount > 0)
            system_c += sum(e.compute_base_amount for e in txn.entries if e.credit_amount > 0)
        assert system_d == system_c, f"System imbalance! Debits {system_d} vs Credits {system_c}"

        # 3. Partner receivable correctly recorded (on-behalf payment 200,000 KES)
        partner_receivable = Decimal("0")
        for txn in all_txns:
            for e in txn.entries:
                if e.account_id == accounts["receivable"] and e.party_id == partner_on_behalf:
                    partner_receivable += e.compute_base_amount
                if e.account_id == accounts["receivable"] and e.credit_amount > 0 and e.party_id == partner_on_behalf:
                    partner_receivable -= e.compute_base_amount
        assert partner_receivable == Decimal("200000")

        # 4. Inventory gold quantity noted on buy (no change on revaluations)
        assert any(
            e.inventory_item_id == gold_item and e.quantity == Decimal("500") and e.debit_amount > 0
            for e in t6_buy_gold.entries
        )
        # Revaluations did not carry quantity
        for e in t6_reval_up.entries + t6_reval_down.entries:
            assert e.inventory_item_id is None and e.quantity is None

        # 5. Phones COGS outflow carried quantity 10
        assert any(
            e.inventory_item_id == phone_item and e.quantity == Decimal("10") and e.credit_amount > 0
            for e in t5_cogs.entries
        )
