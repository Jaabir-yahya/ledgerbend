"""Ledger page - Browse journal entries."""
import streamlit as st
import pandas as pd
from api_client import api

st.markdown('<p class="main-header">📒 Ledger</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Browse journal entries by any dimension</p>', unsafe_allow_html=True)

# Load reference data
@st.cache_data(ttl=300)
def load_reference_data():
    try:
        accounts = api.get_accounts()
        parties = api.get_parties()
        inventory = api.get_inventory()
        return accounts, parties, inventory
    except:
        return [], [], []

accounts, parties, inventory = load_reference_data()

# Filters
st.subheader("Filters")

col1, col2, col3 = st.columns(3)

with col1:
    account_options = {"(All)": None}
    account_options.update({f"{a['code']} - {a['name']}": a['id'] for a in accounts})
    account_sel = st.selectbox("Account", options=list(account_options.keys()))
    account_id = account_options.get(account_sel)

with col2:
    party_options = {"(All)": None}
    party_options.update({f"{p['name']} ({p['type']})": p['id'] for p in parties})
    party_sel = st.selectbox("Party", options=list(party_options.keys()))
    party_id = party_options.get(party_sel)

with col3:
    inv_options = {"(All)": None}
    inv_options.update({f"{i['name']}": i['id'] for i in inventory})
    inv_sel = st.selectbox("Inventory Item", options=list(inv_options.keys()))
    inventory_id = inv_options.get(inv_sel)

col1, col2, col3 = st.columns(3)

with col1:
    currency = st.selectbox("Currency", options=["(All)", "KES", "USD", "EUR", "GBP"])
    currency_code = None if currency == "(All)" else currency

with col2:
    start_date = st.date_input("Start Date", value=None)

with col3:
    end_date = st.date_input("End Date", value=None)

# Search
if st.button("🔍 Search Ledger", type="primary"):
    try:
        entries = api.get_ledger(
            account_id=account_id,
            party_id=party_id,
            inventory_item_id=inventory_id,
            currency_code=currency_code,
            start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
            end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
            limit=100
        )
        
        if entries:
            df = pd.DataFrame(entries)
            
            # Format dates
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            # Create display columns
            df['debit_display'] = df.apply(
                lambda x: f"{x['currency_code']} {x['debit_amount']:,.2f}" if x['debit_amount'] > 0 else "",
                axis=1
            )
            df['credit_display'] = df.apply(
                lambda x: f"{x['currency_code']} {x['credit_amount']:,.2f}" if x['credit_amount'] > 0 else "",
                axis=1
            )
            df['base_display'] = df['base_amount'].apply(lambda x: f"KES {x:,.2f}")
            
            # Select columns for display
            display_cols = [
                'date', 'transaction_number', 'account_code', 'account_name',
                'debit_display', 'credit_display', 'base_display', 'memo'
            ]
            
            # Add optional columns if they exist
            if 'party_name' in df.columns:
                display_cols.insert(4, 'party_name')
            if 'inventory_name' in df.columns:
                display_cols.insert(5, 'inventory_name')
            
            display_df = df[[c for c in display_cols if c in df.columns]].copy()
            
            # Rename columns
            rename_map = {
                'date': 'Date',
                'transaction_number': 'Transaction #',
                'account_code': 'Acct Code',
                'account_name': 'Account',
                'party_name': 'Party',
                'inventory_name': 'Inventory',
                'debit_display': 'Debit',
                'credit_display': 'Credit',
                'base_display': 'Base (KES)',
                'memo': 'Memo'
            }
            display_df.rename(columns=rename_map, inplace=True)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Summary
            st.divider()
            st.subheader("Summary")
            
            total_debits = df['debit_amount'].sum()
            total_credits = df['credit_amount'].sum()
            total_base = df['base_amount'].sum()
            
            sum_col1, sum_col2, sum_col3 = st.columns(3)
            with sum_col1:
                st.metric("Total Debits", f"{total_debits:,.2f}")
            with sum_col2:
                st.metric("Total Credits", f"{total_credits:,.2f}")
            with sum_col3:
                st.metric("Net Base Amount", f"KES {total_base:,.2f}")
            
            # Export option
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"ledger_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No entries found matching your criteria")
            
    except Exception as e:
        st.error(f"Error loading ledger: {e}")

# Quick filters section
st.divider()
st.subheader("Quick Filters")

quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

with quick_col1:
    if st.button("📊 All Entries", use_container_width=True):
        st.session_state['ledger_filter'] = 'all'

with quick_col2:
    if st.button("💰 Cash Accounts", use_container_width=True):
        st.session_state['ledger_filter'] = 'cash'

with quick_col3:
    if st.button("🏢 Receivables", use_container_width=True):
        st.session_state['ledger_filter'] = 'receivables'

with quick_col4:
    if st.button("📦 Inventory", use_container_width=True):
        st.session_state['ledger_filter'] = 'inventory'
