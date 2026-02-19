"""Dashboard page - Overview and key metrics."""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from api_client import api

st.markdown('<p class="main-header">📊 Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Overview of your financial position</p>', unsafe_allow_html=True)

# Check API connection
try:
    health = api.health_check()
    if health.get("status") != "ok":
        st.error("⚠️ API is not responding correctly")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Cannot connect to API: {e}")
    st.info("Please check that the backend is running and API_BASE_URL is configured correctly.")
    st.stop()

# Fetch data
try:
    # Balance verification
    balance_check = api.verify_balance()
    
    # Summary reports
    income_summary = api.get_income_statement_summary()
    balance_sheet_summary = api.get_balance_sheet_summary()
    
    # Lists for counts
    accounts = api.get_accounts()
    parties = api.get_parties()
    inventory = api.get_inventory()
    recent_transactions = api.get_transactions(limit=5)
    
except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.stop()

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Accounts",
        value=len(accounts),
        help="Chart of accounts"
    )

with col2:
    st.metric(
        label="Parties",
        value=len(parties),
        help="Customers, suppliers, agents"
    )

with col3:
    st.metric(
        label="Inventory Items",
        value=len(inventory),
        help="Products and stock items"
    )

with col4:
    st.metric(
        label="Recent Transactions",
        value=len(recent_transactions),
        help="Last 5 transactions"
    )

st.divider()

# Financial health row
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Financial Position")
    
    if income_summary:
        net_profit = income_summary.get("net_profit", 0)
        profit_margin = income_summary.get("profit_margin", 0)
        
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric(
                label="Net Profit (KES)",
                value=f"KES {net_profit:,.2f}",
                delta=f"{profit_margin:.1f}% margin"
            )
        
        with metric_col2:
            total_income = income_summary.get("total_income", 0)
            total_expenses = income_summary.get("total_expenses", 0)
            st.metric(
                label="Income vs Expenses",
                value=f"KES {total_income - total_expenses:,.2f}",
                delta=f"+{total_income:,.0f} / -{total_expenses:,.0f}"
            )
    
    if balance_sheet_summary:
        st.divider()
        
        total_assets = balance_sheet_summary.get("total_assets", 0)
        total_liabilities = balance_sheet_summary.get("total_liabilities", 0)
        total_equity = balance_sheet_summary.get("total_equity", 0)
        is_balanced = balance_sheet_summary.get("is_balanced", False)
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric(label="Assets", value=f"KES {total_assets:,.2f}")
        with metric_col2:
            st.metric(label="Liabilities", value=f"KES {total_liabilities:,.2f}")
        with metric_col3:
            st.metric(label="Equity", value=f"KES {total_equity:,.2f}")
        
        if is_balanced:
            st.success("✅ Balance Sheet is balanced (Assets = Liabilities + Equity)")
        else:
            st.error("❌ Balance Sheet is NOT balanced!")

with col2:
    st.subheader("🛡️ Ledger Integrity")
    
    if balance_check:
        is_valid = balance_check.get("is_valid", False)
        total_debits = balance_check.get("total_debits", 0)
        total_credits = balance_check.get("total_credits", 0)
        
        if is_valid:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown("### ✅ Ledger is Balanced")
            st.markdown(f"**Total Debits:** KES {total_debits:,.2f}")
            st.markdown(f"**Total Credits:** KES {total_credits:,.2f}")
            st.markdown("*The Golden Rule: Debits = Credits*")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.markdown("### ❌ Ledger is NOT Balanced!")
            st.markdown(f"**Total Debits:** KES {total_debits:,.2f}")
            st.markdown(f"**Total Credits:** KES {total_credits:,.2f}")
            st.markdown(f"**Difference:** KES {abs(total_debits - total_credits):,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Recent activity and alerts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Recent Transactions")
    
    if recent_transactions:
        df = pd.DataFrame(recent_transactions)
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df['amount'] = df.apply(
            lambda x: f"KES {sum(e.get('base_amount', 0) for e in x['entries'] if e.get('debit_amount', 0) > 0):,.2f}",
            axis=1
        )
        
        display_df = df[['transaction_number', 'date', 'description', 'amount', 'is_posted']].copy()
        display_df.columns = ['Transaction #', 'Date', 'Description', 'Amount', 'Posted']
        display_df['Posted'] = display_df['Posted'].apply(lambda x: '✅' if x else '📝')
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet")

with col2:
    st.subheader("⚡ Quick Actions")
    
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("➕ New Transaction", use_container_width=True):
            st.switch_page("pages/transactions.py")
        
        if st.button("👤 New Party", use_container_width=True):
            st.switch_page("pages/parties.py")
    
    with action_col2:
        if st.button("📊 View Reports", use_container_width=True):
            st.switch_page("pages/reports.py")
        
        if st.button("🎯 Use Cases", use_container_width=True):
            st.switch_page("pages/use_cases.py")

# Currency exposure preview
try:
    currency_exposure = api.get_currency_exposure()
    
    if currency_exposure:
        st.divider()
        st.subheader("💱 Currency Exposure")
        
        df = pd.DataFrame(currency_exposure)
        if not df.empty:
            df['net_base_amount'] = df['net_base_amount'].apply(lambda x: f"KES {x:,.2f}")
            display_df = df[['currency_code', 'net_amount', 'net_base_amount', 'avg_rate']].copy()
            display_df.columns = ['Currency', 'Net Amount', 'Net (KES)', 'Avg Rate']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
except Exception:
    pass  # Silently fail if endpoint not available
