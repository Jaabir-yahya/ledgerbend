"""Use Cases page - Real-world business scenarios and workflows."""
import streamlit as st
import pandas as pd
import json
from datetime import date, timedelta
from api_client import api
import config

st.markdown('<p class="main-header">🎯 Use Cases & Workflows</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Real-world business scenarios demonstrating the full power of the ledger</p>', unsafe_allow_html=True)

# Introduction
st.markdown('<div class="info-box">', unsafe_allow_html=True)
st.markdown("""
**Welcome to the Universal Double-Entry Ledger!**

This page demonstrates real-world business scenarios that showcase:
- Cross-currency transactions (imports, exports, forex)
- Inventory management with average cost tracking
- Agent/Runner tracking for field operations
- Complex multi-party transactions
- Correction workflows using reversals
- Gold and commodity trading

Each scenario includes step-by-step guidance and ready-to-use transaction templates.
""")
st.markdown('</div>', unsafe_allow_html=True)

# Use case tabs
use_cases = st.tabs([
    "🚢 Import Business",
    "🏪 Retail Sales",
    "💱 Forex Trading", 
    "🥇 Gold Trading",
    "🏃 Runner Operations",
    "🔄 Corrections",
    "📅 Month-End",
    "🔧 Advanced"
])

with use_cases[0]:  # Import Business
    st.header("🚢 Import Business Scenario")
    
    st.markdown("""
    **Business Context:** You're importing electronics from Dubai to sell in Kenya.
    You pay in USD, receive goods, sell in KES, and track inventory with average costs.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 1: Capital Injection")
        st.markdown("Owner invests capital to start the business")
        
        step1_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Owner capital injection",
            "reference": "CAPITAL-001",
            "entries": [
                {
                    "account_id": "1100",  # Cash KES
                    "debit_amount": 500000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Initial capital"
                },
                {
                    "account_id": "3100",  # Owner Capital
                    "debit_amount": 0,
                    "credit_amount": 500000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Owner investment"
                }
            ]
        }
        
        with st.expander("View Transaction Payload"):
            st.code(json.dumps(step1_payload, indent=2), language="json")
    
    with col2:
        st.subheader("Step 2: Import Purchase (USD)")
        st.markdown("Purchase inventory from Dubai supplier in USD")
        
        step2_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Import purchase - iPhone shipment from Dubai",
            "reference": "DUBAI-INV-001",
            "entries": [
                {
                    "account_id": "1300",  # Inventory
                    "debit_amount": 2000,
                    "credit_amount": 0,
                    "currency_code": "USD",
                    "exchange_rate": 130.0,
                    "inventory_item_id": "iphone-15-pro",
                    "quantity": 20,
                    "memo": "iPhone 15 Pro x 20 units"
                },
                {
                    "account_id": "5100",  # Freight
                    "debit_amount": 500,
                    "credit_amount": 0,
                    "currency_code": "USD",
                    "exchange_rate": 130.0,
                    "memo": "Shipping and freight"
                },
                {
                    "account_id": "2100",  # Accounts Payable
                    "debit_amount": 0,
                    "credit_amount": 2500,
                    "currency_code": "USD",
                    "exchange_rate": 130.0,
                    "party_id": "dubai-supplier",
                    "memo": "Payable to Dubai supplier"
                }
            ]
        }
        
        with st.expander("View Transaction Payload"):
            st.code(json.dumps(step2_payload, indent=2), language="json")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 3: Record Sales")
        st.markdown("Sell imported goods to customers in KES")
        
        step3_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Sale to local customer",
            "reference": "SALE-001",
            "entries": [
                {
                    "account_id": "1100",  # Cash KES
                    "debit_amount": 350000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Cash sale"
                },
                {
                    "account_id": "4100",  # Sales Income
                    "debit_amount": 0,
                    "credit_amount": 350000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "iPhone sales"
                },
                {
                    "account_id": "5200",  # COGS
                    "debit_amount": 260000,  # 2000 * 130
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "iphone-15-pro",
                    "quantity": -10,
                    "memo": "Cost of goods sold"
                },
                {
                    "account_id": "1300",  # Inventory
                    "debit_amount": 0,
                    "credit_amount": 260000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "iphone-15-pro",
                    "quantity": -10,
                    "memo": "Inventory reduction"
                }
            ]
        }
        
        with st.expander("View Transaction Payload"):
            st.code(json.dumps(step3_payload, indent=2), language="json")
    
    with col2:
        st.subheader("Step 4: Settle Payable")
        st.markdown("Pay Dubai supplier in USD")
        
        step4_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Payment to Dubai supplier",
            "reference": "SWIFT-12345",
            "entries": [
                {
                    "account_id": "2100",  # Accounts Payable
                    "debit_amount": 2500,
                    "credit_amount": 0,
                    "currency_code": "USD",
                    "exchange_rate": 132.0,  # Rate changed!
                    "party_id": "dubai-supplier",
                    "memo": "Full settlement"
                },
                {
                    "account_id": "1110",  # Cash USD
                    "debit_amount": 0,
                    "credit_amount": 2500,
                    "currency_code": "USD",
                    "exchange_rate": 1.0,
                    "memo": "USD cash out"
                },
                {
                    "account_id": "4500",  # FX Trading Gain
                    "debit_amount": 0,
                    "credit_amount": 5000,  # 2500 * (132-130)
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "FX gain on payable settlement"
                }
            ]
        }
        
        with st.expander("View Transaction Payload"):
            st.code(json.dumps(step4_payload, indent=2), language="json")
    
    st.divider()
    st.info("💡 **Key Concepts:** Multi-currency tracking, inventory with average cost, FX gains/losses on settlement")

with use_cases[1]:  # Retail Sales
    st.header("🏪 Retail Business Scenario")
    
    st.markdown("""
    **Business Context:** You run a electronics shop selling phones, accessories, and offering repair services.
    Track inventory, COGS automatically, and handle cash/M-PESA/bank payments.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Cash Sale with Inventory")
        st.markdown("""
        Customer buys iPhone and accessories, pays in cash.
        System automatically:
        - Records revenue
        - Calculates COGS using average cost
        - Reduces inventory quantity
        """)
        
        retail_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Cash sale - iPhone 15 Pro + accessories",
            "reference": "POS-001",
            "entries": [
                {
                    "account_id": "1100",  # Cash KES
                    "debit_amount": 380000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Customer payment"
                },
                {
                    "account_id": "4100",  # Sales
                    "debit_amount": 0,
                    "credit_amount": 350000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "iphone-15-pro",
                    "memo": "iPhone sale"
                },
                {
                    "account_id": "4101",  # Accessories Sales
                    "debit_amount": 0,
                    "credit_amount": 30000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Case + screen protector"
                },
                {
                    "account_id": "5200",  # COGS
                    "debit_amount": 260000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "iphone-15-pro",
                    "quantity": -1,
                    "memo": "COGS auto-calculated"
                },
                {
                    "account_id": "1300",  # Inventory
                    "debit_amount": 0,
                    "credit_amount": 260000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "iphone-15-pro",
                    "quantity": -1,
                    "memo": "Stock out"
                },
                {
                    "account_id": "5201",  # COGS Accessories
                    "debit_amount": 15000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "accessories",
                    "quantity": -2,
                    "memo": "Accessories COGS"
                },
                {
                    "account_id": "1301",  # Inventory Accessories
                    "debit_amount": 0,
                    "credit_amount": 15000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "accessories",
                    "quantity": -2,
                    "memo": "Stock out accessories"
                }
            ]
        }
        
        with st.expander("View Full Transaction"):
            st.code(json.dumps(retail_payload, indent=2), language="json")
    
    with col2:
        st.subheader("M-PESA Payment")
        st.markdown("""
        Customer pays via M-PESA.
        Track separately from cash for reconciliation.
        """)
        
        mpesa_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "M-PESA sale - Samsung phone",
            "reference": "MPESA-QW12E34",
            "entries": [
                {
                    "account_id": "1150",  # M-PESA
                    "debit_amount": 85000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "M-PESA payment received"
                },
                {
                    "account_id": "4100",  # Sales
                    "debit_amount": 0,
                    "credit_amount": 85000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Samsung phone sale"
                }
            ]
        }
        
        with st.expander("View M-PESA Transaction"):
            st.code(json.dumps(mpesa_payload, indent=2), language="json")
    
    st.divider()
    
    # Payment methods comparison
    st.subheader("Payment Methods Supported")
    
    payment_df = pd.DataFrame({
        'Method': ['Cash', 'M-PESA', 'Bank Transfer', 'Credit (On Account)', 'Mobile Money (Other)'],
        'Account Code': ['1100', '1150', '1200', '2100', '1160'],
        'Account Name': ['Cash KES', 'M-PESA', 'Bank KES', 'Accounts Payable', 'Airtel Money'],
        'Reconciliation': ['Daily count', 'M-PESA statement', 'Bank statement', 'Aging report', 'Provider statement']
    })
    
    st.dataframe(payment_df, use_container_width=True, hide_index=True)
    
    st.info("💡 **Key Concepts:** Automated COGS calculation, multi-payment-method tracking, inventory quantity updates")

with use_cases[2]:  # Forex Trading
    st.header("💱 Forex Trading Bureau Scenario")
    
    st.markdown("""
    **Business Context:** You run a forex bureau buying and selling foreign currency.
    Track multiple currency positions, average exchange rates, and realized/unrealized gains.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Buying USD (Stocking Up)")
        st.markdown("Buy USD from customers with KES")
        
        buy_usd_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Purchase USD 10,000 from customer",
            "reference": "FX-BUY-001",
            "entries": [
                {
                    "account_id": "1110",  # Cash USD
                    "debit_amount": 10000,
                    "credit_amount": 0,
                    "currency_code": "USD",
                    "exchange_rate": 129.50,
                    "memo": "Buying USD"
                },
                {
                    "account_id": "1100",  # Cash KES
                    "debit_amount": 0,
                    "credit_amount": 1295000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Paying KES 1,295,000"
                }
            ]
        }
        
        with st.expander("View Transaction"):
            st.code(json.dumps(buy_usd_payload, indent=2), language="json")
    
    with col2:
        st.subheader("Selling USD (Customer Purchase)")
        st.markdown("Sell USD to customer, take KES")
        
        sell_usd_payload = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Sell USD 5,000 to customer",
            "reference": "FX-SELL-001",
            "entries": [
                {
                    "account_id": "1100",  # Cash KES
                    "debit_amount": 662500,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Receiving KES 662,500 @ 132.50"
                },
                {
                    "account_id": "1110",  # Cash USD
                    "debit_amount": 0,
                    "credit_amount": 5000,
                    "currency_code": "USD",
                    "exchange_rate": 1.0,
                    "memo": "Selling USD"
                },
                {
                    "account_id": "4500",  # FX Trading Gain
                    "debit_amount": 0,
                    "credit_amount": 15000,  # 5000 * (132.50 - 129.50)
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Spread profit"
                }
            ]
        }
        
        with st.expander("View Transaction"):
            st.code(json.dumps(sell_usd_payload, indent=2), language="json")
    
    st.divider()
    
    # FX Position tracking
    st.subheader("Understanding FX Position Tracking")
    
    st.markdown("""
    The system automatically tracks:
    1. **Average Rate:** Weighted average of all purchases
    2. **Net Position:** Current holdings of each currency
    3. **Unrealized P&L:** Current market value vs. average cost
    4. **Realized P&L:** Profit from completed trades
    
    **Example Position Table:**
    """)
    
    position_df = pd.DataFrame({
        'Currency': ['USD', 'EUR', 'GBP'],
        'Net Amount': [5000, 2000, 1000],
        'Avg Rate': [129.50, 140.20, 165.80],
        'Current Rate': [132.00, 142.50, 168.00],
        'Base Value (KES)': [647500, 280400, 165800],
        'Market Value': [660000, 285000, 168000],
        'Unrealized P&L': [+12500, +4600, +2200]
    })
    
    st.dataframe(position_df, use_container_width=True, hide_index=True)
    
    st.info("💡 **Key Concepts:** Average cost tracking, realized vs unrealized gains, multi-currency positions")

with use_cases[3]:  # Gold Trading
    st.header("🥇 Gold Trading Scenario")
    
    st.markdown("""
    **Business Context:** Trading physical gold as a volatile asset.
    Track quantity in grams, average cost per gram, and mark-to-market revaluations.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Gold Purchase")
        st.markdown("Buy 100g of 24K gold at KES 8,000/gram")
        
        gold_buy = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Purchase 100g 24K Gold",
            "reference": "GOLD-BUY-001",
            "entries": [
                {
                    "account_id": "1350",  # Gold Inventory (marked as volatile)
                    "debit_amount": 800000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "gold-24k",
                    "quantity": 100,
                    "memo": "100g @ KES 8,000/g"
                },
                {
                    "account_id": "1100",  # Cash KES
                    "debit_amount": 0,
                    "credit_amount": 800000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Payment for gold"
                }
            ]
        }
        
        with st.expander("View Transaction"):
            st.code(json.dumps(gold_buy, indent=2), language="json")
    
    with col2:
        st.subheader("Mark-to-Market Revaluation")
        st.markdown("Price rose to KES 8,500/gram. Revalue inventory.")
        
        gold_revalue = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Gold mark-to-market revaluation",
            "reference": "GOLD-REVAL-001",
            "entries": [
                {
                    "account_id": "1350",  # Gold Inventory
                    "debit_amount": 50000,  # 100g * (8500-8000)
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Unrealized gain on gold"
                },
                {
                    "account_id": "4550",  # Unrealized Gain
                    "debit_amount": 0,
                    "credit_amount": 50000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Gold revaluation"
                }
            ]
        }
        
        with st.expander("View Revaluation"):
            st.code(json.dumps(gold_revalue, indent=2), language="json")
    
    st.divider()
    
    st.subheader("Gold Position Tracking")
    
    gold_df = pd.DataFrame({
        'Metric': ['Current Quantity', 'Average Cost/g', 'Current Market Price/g', 
                   'Total Cost Basis', 'Current Market Value', 'Unrealized P&L'],
        'Value': ['100g', 'KES 8,000', 'KES 8,500', 'KES 800,000', 'KES 850,000', '+KES 50,000'],
        'Notes': ['', 'Avg of all purchases', 'Latest market rate', 'Historical cost', 'Current value', 'Paper gain']
    })
    
    st.dataframe(gold_df, use_container_width=True, hide_index=True)
    
    st.warning("⚠️ **Note:** Mark 'Gold' inventory item as `is_volatile=true` in the database to enable revaluation workflows")
    
    st.info("💡 **Key Concepts:** Volatile asset tracking, mark-to-market accounting, unrealized gains")

with use_cases[4]:  # Runner Operations
    st.header("🏃 Runner/Field Agent Scenario")
    
    st.markdown("""
    **Business Context:** You send agents (runners) to upcountry areas with cash to buy goods 
    or collect payments. Track money sent, expenses incurred, and goods returned.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Send Cash with Runner")
        st.markdown("Send KES 50,000 with Agent John to buy maize upcountry")
        
        send_runner = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Cash sent with Runner John for upcountry purchasing",
            "reference": "RUNNER-001",
            "entries": [
                {
                    "account_id": "1180",  # Cash with Runner (asset)
                    "debit_amount": 50000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "party_id": "runner-john",
                    "memo": "Float for maize purchase"
                },
                {
                    "account_id": "1100",  # Cash KES
                    "debit_amount": 0,
                    "credit_amount": 50000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Cash handed to runner"
                }
            ]
        }
        
        with st.expander("View Transaction"):
            st.code(json.dumps(send_runner, indent=2), language="json")
    
    with col2:
        st.subheader("Runner Returns with Goods")
        st.markdown("Runner returns with maize worth KES 42,000 and KES 5,000 cash. Spent KES 3,000 on transport.")
        
        runner_return = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Runner return - maize purchase",
            "reference": "RUNNER-001-RETURN",
            "entries": [
                {
                    "account_id": "1300",  # Inventory - Maize
                    "debit_amount": 42000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "maize",
                    "quantity": 100,  # 100 bags
                    "memo": "Maize purchased upcountry"
                },
                {
                    "account_id": "5400",  # Transport Expense
                    "debit_amount": 3000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "party_id": "runner-john",
                    "memo": "Transport costs"
                },
                {
                    "account_id": "1100",  # Cash KES (returned)
                    "debit_amount": 5000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Cash returned"
                },
                {
                    "account_id": "1180",  # Cash with Runner
                    "debit_amount": 0,
                    "credit_amount": 50000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "party_id": "runner-john",
                    "memo": "Clear runner float"
                }
            ]
        }
        
        with st.expander("View Return Transaction"):
            st.code(json.dumps(runner_return, indent=2), language="json")
    
    st.divider()
    
    st.subheader("Runner Tracking Summary")
    
    runner_df = pd.DataFrame({
        'Runner': ['John', 'Mary', 'Peter'],
        'Status': ['Available', 'On Assignment', 'Available'],
        'Current Float': ['KES 0', 'KES 75,000', 'KES 0'],
        'Last Trip': ['2024-01-15', 'Active', '2024-01-10'],
        'YTD Expenses': ['KES 12,000', 'KES 3,000', 'KES 8,500']
    })
    
    st.dataframe(runner_df, use_container_width=True, hide_index=True)
    
    st.info("💡 **Key Concepts:** Float tracking, expense allocation, party-based accountability")

with use_cases[5]:  # Corrections
    st.header("🔄 Correction & Reversal Workflows")
    
    st.markdown("""
    **Important Principle:** The ledger is immutable. Posted transactions cannot be edited.
    Corrections are made by reversing the original transaction and creating a new correct one.
    This maintains audit trail integrity.
    """)
    
    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
    st.markdown("""
    **Never Edit Posted Transactions!**
    
    The Golden Rule of Double-Entry:
    1. Original transaction stays as-is (audit trail)
    2. Create reversal transaction (flips all debits/credits)
    3. Create new correct transaction
    4. Link reversal to original for traceability
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Example: Wrong Amount Posted")
        st.markdown("Posted KES 100,000 instead of KES 10,000")
        
        st.markdown("**Step 1: Original (Wrong)**")
        wrong_txn = {
            "transaction_number": "TXN-2024-001",
            "description": "Supplier payment",
            "entries": [
                {"account": "Payables", "debit": 100000, "credit": 0},
                {"account": "Cash", "debit": 0, "credit": 100000}
            ]
        }
        st.code(json.dumps(wrong_txn, indent=2), language="json")
        
        st.markdown("**Step 2: Reversal**")
        st.code("""
POST /api/v1/transactions/{id}/reverse

Response:
{
  "transaction_number": "TXN-2024-002",
  "is_reversal": true,
  "reverses_transaction_id": "TXN-2024-001",
  "description": "Reversal of TXN-2024-001",
  "entries": [
    {"account": "Payables", "debit": 0, "credit": 100000},  // Flipped!
    {"account": "Cash", "debit": 100000, "credit": 0}       // Flipped!
  ]
}
        """, language="json")
    
    with col2:
        st.subheader("Step 3: Correct Entry")
        st.markdown("Post the correct transaction")
        
        correct_txn = {
            "date": date.today().strftime('%Y-%m-%d'),
            "description": "Supplier payment - CORRECTED",
            "reference": "CORRECTION-001",
            "entries": [
                {
                    "account_id": "2100",  # Payables
                    "debit_amount": 10000,   // Correct amount!
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Correct payment amount"
                },
                {
                    "account_id": "1100",  # Cash
                    "debit_amount": 0,
                    "credit_amount": 10000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Correct payment"
                }
            ]
        }
        
        with st.expander("View Correct Transaction"):
            st.code(json.dumps(correct_txn, indent=2), language="json")
    
    st.divider()
    
    st.subheader("Common Correction Scenarios")
    
    corrections_df = pd.DataFrame({
        'Scenario': [
            'Wrong amount',
            'Wrong account',
            'Wrong date',
            'Wrong party',
            'Wrong currency',
            'Forgot inventory quantity',
            'Double-posted'
        ],
        'Fix Method': [
            'Reverse + new transaction',
            'Reverse + new transaction',
            'Reverse + new transaction',
            'Reverse + new transaction',
            'Reverse + new transaction',
            'Reverse + new with quantity',
            'Reverse one instance'
        ],
        'Prevention': [
            'Validate amounts before posting',
            'Use account dropdowns',
            'Use date pickers',
            'Verify party selection',
            'Double-check currency',
            'Always enter quantity',
            'Check for duplicates'
        ]
    })
    
    st.dataframe(corrections_df, use_container_width=True, hide_index=True)
    
    st.info("💡 **Key Concepts:** Immutability, audit trails, reversal chains, accountability")

with use_cases[6]:  # Month-End
    st.header("📅 Month-End Close Process")
    
    st.markdown("""
    **Month-End Checklist:** Steps to close the books each month.
    """)
    
    checklist = [
        ("1. Review & Post Drafts", "Ensure all transactions are posted, no drafts remaining"),
        ("2. Bank Reconciliation", "Match cash accounts to bank statements"),
        ("3. M-PESA Reconciliation", "Reconcile M-PESA account to Safaricom statement"),
        ("4. Inventory Count", "Physical count matches system quantities"),
        ("5. Party Balances", "Confirm receivables/payables with parties"),
        ("6. Verify Balance", "Run verify-balance to check debits = credits"),
        ("7. Trial Balance", "Review trial balance for anomalies"),
        ("8. Financial Statements", "Generate P&L and Balance Sheet"),
        ("9. Adjusting Entries", "Accruals, prepayments, depreciation"),
        ("10. Close Period", "Lock the period (when implemented)")
    ]
    
    for title, desc in checklist:
        with st.expander(title):
            st.markdown(desc)
            
            if "Verify Balance" in title:
                st.markdown("**API Call:**")
                st.code("GET /api/v1/reports/verify-balance", language="bash")
                st.markdown("**Expected Response:**")
                st.code(json.dumps({
                    "is_valid": True,
                    "total_debits": 15000000.00,
                    "total_credits": 15000000.00,
                    "difference": 0.00
                }, indent=2), language="json")
    
    st.divider()
    
    st.subheader("Month-End Reports Dashboard")
    
    report_col1, report_col2, report_col3 = st.columns(3)
    
    with report_col1:
        st.markdown("**Verify Ledger Integrity**")
        st.code("GET /api/v1/reports/verify-balance")
        st.markdown("✅ Must return `is_valid: true`")
    
    with report_col2:
        st.markdown("**Trial Balance**")
        st.code("GET /api/v1/reports/trial-balance")
        st.markdown("📊 Check account balances")
    
    with report_col3:
        st.markdown("**Financial Statements**")
        st.code("GET /api/v1/reports/income-statement\nGET /api/v1/reports/balance-sheet")
        st.markdown("📈 Review P&L and BS")
    
    st.info("💡 **Key Concepts:** Period closing, reconciliation, verification, adjusting entries")

with use_cases[7]:  # Advanced
    st.header("🔧 Advanced Scenarios")
    
    st.markdown("Complex business scenarios requiring multiple accounts and careful structuring.")
    
    st.subheader("On-Behalf Payment (Multi-Party)")
    st.markdown("""
    **Scenario:** You pay KES 50,000 to Supplier A on behalf of Partner B.
    Partner B will reimburse you later.
    """)
    
    onbehalf = {
        "date": date.today().strftime('%Y-%m-%d'),
        "description": "Paid Supplier A on behalf of Partner B",
        "reference": "ONBEHALF-001",
        "entries": [
            {
                "account_id": "2200",  # Partner Receivable
                "debit_amount": 50000,
                "credit_amount": 0,
                "currency_code": "KES",
                "exchange_rate": 1.0,
                "party_id": "partner-b",
                "memo": "Payment on behalf - to be reimbursed"
            },
            {
                "account_id": "1100",  # Cash KES
                "debit_amount": 0,
                "credit_amount": 50000,
                "currency_code": "KES",
                "exchange_rate": 1.0,
                "memo": "Payment to Supplier A"
            }
        ]
    }
    
    with st.expander("View On-Behalf Transaction"):
        st.code(json.dumps(onbehalf, indent=2), language="json")
    
    st.divider()
    
    st.subheader("Complex Import with Multiple Costs")
    st.markdown("Purchase with product cost + freight + insurance + duty")
    
    complex_import = {
        "date": date.today().strftime('%Y-%m-%d'),
        "description": "Import shipment - electronics with all costs",
        "reference": "IMPORT-COMPLEX-001",
        "entries": [
            {
                "account_id": "1300",  # Inventory (landed cost)
                "debit_amount": 15000,
                "credit_amount": 0,
                "currency_code": "USD",
                "exchange_rate": 130.0,
                "inventory_item_id": "electronics",
                "quantity": 50,
                "memo": "Product cost: 10,000 + Freight: 3,000 + Insurance: 1,000 + Duty: 1,000"
            },
            {
                "account_id": "2100",  # Payables - Supplier
                "debit_amount": 0,
                "credit_amount": 10000,
                "currency_code": "USD",
                "exchange_rate": 130.0,
                "party_id": "supplier",
                "memo": "Product cost"
            },
            {
                "account_id": "2110",  # Payables - Freight Forwarder
                "debit_amount": 0,
                "credit_amount": 3000,
                "currency_code": "USD",
                "exchange_rate": 130.0,
                "party_id": "freight-co",
                "memo": "Freight charges"
            },
            {
                "account_id": "2120",  # Payables - Insurance
                "debit_amount": 0,
                "credit_amount": 1000,
                "currency_code": "USD",
                "exchange_rate": 130.0,
                "party_id": "insurance-co",
                "memo": "Insurance"
            },
            {
                "account_id": "2130",  # Payables - KRA (Duty)
                "debit_amount": 0,
                "credit_amount": 1000,
                "currency_code": "USD",
                "exchange_rate": 130.0,
                "party_id": "kra",
                "memo": "Import duty"
            }
        ]
    }
    
    with st.expander("View Complex Import"):
        st.code(json.dumps(complex_import, indent=2), language="json")
    
    st.divider()
    
    st.subheader("API Quick Reference")
    
    quick_ref = pd.DataFrame({
        'Endpoint': [
            'POST /transactions',
            'GET /transactions',
            'POST /transactions/{id}/reverse',
            'GET /ledger',
            'GET /reports/trial-balance',
            'GET /reports/income-statement',
            'GET /reports/balance-sheet',
            'GET /reports/verify-balance'
        ],
        'Purpose': [
            'Create transaction',
            'List transactions',
            'Reverse transaction',
            'Browse entries',
            'Trial balance',
            'P&L report',
            'Balance sheet',
            'Verify ledger integrity'
        ],
        'Key Params': [
            'date, description, entries[]',
            'start_date, end_date, limit',
            'none (path param)',
            'account_id, party_id, date range',
            'none',
            'start_date, end_date',
            'date_to',
            'none'
        ]
    })
    
    st.dataframe(quick_ref, use_container_width=True, hide_index=True)

st.divider()

# Footer with philosophy
st.markdown('<div class="success-box">', unsafe_allow_html=True)
st.markdown("""
### 🎯 The Philosophy

**Phase 1: The Truth Layer**
- Log any financial mess accurately now
- Unlock infinite reporting possibilities later
- Once it's in the system, you can analyze it
- Corrections are transparent (never hidden edits)

**For Solo Entrepreneurs:**
This system is designed for you - someone who needs to track everything 
from cash sales to complex imports, without an accounting degree.

**Immutable = Trustworthy:**
Every transaction leaves a trail. Every correction is documented. 
Your books tell the complete story.
""")
st.markdown('</div>', unsafe_allow_html=True)
