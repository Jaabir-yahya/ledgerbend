"""Accounts page - Manage chart of accounts."""
import streamlit as st
import pandas as pd
from api_client import api
import config

st.markdown('<p class="main-header">📋 Accounts</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Chart of Accounts management</p>', unsafe_allow_html=True)

tab_list, tab_create = st.tabs(["📊 View Accounts", "➕ Create Account"])

with tab_list:
    st.subheader("Chart of Accounts")
    
    # Filter by type
    account_type = st.selectbox(
        "Filter by Type",
        options=["All"] + config.ACCOUNT_TYPES,
        format_func=lambda x: x.title() if x != "All" else "All Accounts"
    )
    
    try:
        accounts = api.get_accounts(type=account_type if account_type != "All" else None)
        
        if accounts:
            df = pd.DataFrame(accounts)
            
            # Format for display
            df['type'] = df['type'].str.title()
            df['normal_balance'] = df['normal_balance'].str.upper()
            
            # Color coding by type
            def color_type(val):
                colors = {
                    'Asset': 'background-color: #d4edda',
                    'Liability': 'background-color: #f8d7da',
                    'Equity': 'background-color: #d1ecf1',
                    'Income': 'background-color: #fff3cd',
                    'Expense': 'background-color: #f0f0f0'
                }
                return colors.get(val, '')
            
            display_df = df[['code', 'name', 'type', 'normal_balance', 'is_active']].copy()
            display_df.columns = ['Code', 'Name', 'Type', 'Normal Balance', 'Active']
            display_df['Active'] = display_df['Active'].apply(lambda x: '✅' if x else '❌')
            
            # Group by type
            for acct_type in config.ACCOUNT_TYPES:
                type_accounts = display_df[display_df['Type'].str.lower() == acct_type]
                if not type_accounts.empty:
                    with st.expander(f"{acct_type.title()} Accounts ({len(type_accounts)})", expanded=True):
                        st.dataframe(type_accounts.drop('Type', axis=1), 
                                   use_container_width=True, hide_index=True)
        else:
            st.info("No accounts found")
    except Exception as e:
        st.error(f"Error loading accounts: {e}")

with tab_create:
    st.subheader("Create New Account")
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **Chart of Accounts Structure:**
    - **Assets (1000s):** Cash, Bank, Receivables, Inventory, Equipment
    - **Liabilities (2000s):** Payables, Loans, Accruals
    - **Equity (3000s):** Capital, Retained Earnings
    - **Income (4000s):** Sales, Interest, Other Income
    - **Expenses (5000s):** COGS, Operating Expenses
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        code = st.text_input("Account Code", placeholder="e.g., 1100, 2100, 5100")
        name = st.text_input("Account Name", placeholder="e.g., Cash - USD, Office Rent")
    
    with col2:
        acct_type = st.selectbox("Account Type", options=config.ACCOUNT_TYPES, format_func=lambda x: x.title())
        
        # Normal balance based on type
        if acct_type in ['asset', 'expense']:
            default_normal = 'debit'
        else:
            default_normal = 'credit'
        
        normal_balance = st.selectbox(
            "Normal Balance",
            options=['debit', 'credit'],
            index=0 if default_normal == 'debit' else 1,
            help="Which side increases this account"
        )
    
    is_active = st.checkbox("Active Account", value=True)
    
    if st.button("💾 Create Account", type="primary"):
        if code and name and acct_type:
            try:
                payload = {
                    "code": code,
                    "name": name,
                    "type": acct_type,
                    "normal_balance": normal_balance,
                    "is_active": is_active
                }
                
                result = api.create_account(payload)
                
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown("### ✅ Account Created!")
                st.markdown(f"**Code:** {result.get('code')}")
                st.markdown(f"**Name:** {result.get('name')}")
                st.markdown(f"**Type:** {result.get('type')}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error creating account: {e}")
        else:
            st.warning("Please fill in all required fields")

# Account summary cards
st.divider()
st.subheader("Account Summary")

try:
    all_accounts = api.get_accounts()
    
    if all_accounts:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        type_counts = {}
        for acct in all_accounts:
            t = acct.get('type', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        
        with col1:
            st.metric("Assets", type_counts.get('asset', 0))
        with col2:
            st.metric("Liabilities", type_counts.get('liability', 0))
        with col3:
            st.metric("Equity", type_counts.get('equity', 0))
        with col4:
            st.metric("Income", type_counts.get('income', 0))
        with col5:
            st.metric("Expenses", type_counts.get('expense', 0))
except Exception:
    pass
