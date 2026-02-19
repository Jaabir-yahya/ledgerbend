"""Transactions page - Create and manage transactions."""
import streamlit as st
import pandas as pd
from datetime import date
from api_client import api
import config
import json

st.markdown('<p class="main-header">💰 Transactions</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Create, view, and reverse financial transactions</p>', unsafe_allow_html=True)

# Tabs for different functions
tab_list, tab_create, tab_detail = st.tabs(["📋 List Transactions", "➕ Create Transaction", "🔍 Transaction Detail"])

with tab_list:
    st.subheader("Browse Transactions")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", value=None, key="list_start")
    with col2:
        end_date = st.date_input("End Date", value=None, key="list_end")
    with col3:
        limit = st.number_input("Limit", min_value=1, max_value=100, value=20)
    
    if st.button("🔍 Search", key="search_btn"):
        try:
            transactions = api.get_transactions(
                start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
                end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
                limit=limit
            )
            
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df['total_amount'] = df.apply(
                    lambda x: sum(e.get('base_amount', 0) for e in x['entries'] if e.get('debit_amount', 0) > 0),
                    axis=1
                )
                
                display_df = df[['id', 'transaction_number', 'date', 'description', 'total_amount', 'is_posted', 'reference']].copy()
                display_df.columns = ['ID', 'Transaction #', 'Date', 'Description', 'Amount (KES)', 'Posted', 'Reference']
                display_df['Posted'] = display_df['Posted'].apply(lambda x: '✅ Yes' if x else '📝 Draft')
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Store for detail view
                st.session_state['transactions_list'] = transactions
            else:
                st.info("No transactions found")
        except Exception as e:
            st.error(f"Error loading transactions: {e}")

with tab_create:
    st.subheader("Create New Transaction")
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **Transaction Rules:**
    - Total debits must equal total credits
    - Each entry must have either debit OR credit, not both
    - Once posted, transactions are immutable (use reversal to correct)
    - Cross-currency transactions are automatically converted to base currency (KES)
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        txn_date = st.date_input("Transaction Date", value=date.today())
        description = st.text_input("Description", placeholder="e.g., Purchase of inventory from Dubai")
    with col2:
        reference = st.text_input("Reference", placeholder="e.g., INV-2024-001, SWIFT-12345")
    
    st.divider()
    
    # Load reference data
    try:
        accounts = api.get_accounts()
        parties = api.get_parties()
        inventory_items = api.get_inventory()
    except Exception as e:
        st.error(f"Error loading reference data: {e}")
        accounts, parties, inventory_items = [], [], []
    
    # Build entries
    st.subheader("Journal Entries")
    
    num_entries = st.number_input("Number of Entries", min_value=2, max_value=10, value=2)
    
    entries = []
    total_debits = 0
    total_credits = 0
    
    for i in range(int(num_entries)):
        st.markdown(f"**Entry {i+1}**")
        
        cols = st.columns([2, 1, 1, 1, 1, 1, 1])
        
        with cols[0]:
            account_options = {f"{a['code']} - {a['name']}": a['id'] for a in accounts}
            account_sel = st.selectbox(
                f"Account {i+1}",
                options=list(account_options.keys()),
                key=f"acct_{i}"
            )
            account_id = account_options.get(account_sel)
        
        with cols[1]:
            entry_type = st.selectbox(
                f"Type {i+1}",
                options=["debit", "credit"],
                key=f"type_{i}"
            )
        
        with cols[2]:
            amount = st.number_input(
                f"Amount {i+1}",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key=f"amt_{i}"
            )
        
        with cols[3]:
            currency = st.selectbox(
                f"Currency {i+1}",
                options=config.CURRENCIES,
                index=0,
                key=f"curr_{i}"
            )
        
        with cols[4]:
            exchange_rate = st.number_input(
                f"Rate {i+1}",
                min_value=0.0001,
                value=1.0 if currency == "KES" else 130.0,
                step=0.01,
                key=f"rate_{i}"
            )
        
        with cols[5]:
            party_options = {"(None)": None}
            party_options.update({f"{p['name']} ({p['type']})": p['id'] for p in parties})
            party_sel = st.selectbox(
                f"Party {i+1}",
                options=list(party_options.keys()),
                key=f"party_{i}"
            )
            party_id = party_options.get(party_sel)
        
        with cols[6]:
            inv_options = {"(None)": None}
            inv_options.update({f"{inv['name']}": inv['id'] for inv in inventory_items})
            inv_sel = st.selectbox(
                f"Inventory {i+1}",
                options=list(inv_options.keys()),
                key=f"inv_{i}"
            )
            inventory_id = inv_options.get(inv_sel)
        
        # Calculate
        if entry_type == "debit":
            total_debits += amount * exchange_rate
            debit_amt = amount
            credit_amt = 0
        else:
            total_credits += amount * exchange_rate
            debit_amt = 0
            credit_amt = amount
        
        # Quantity if inventory
        quantity = None
        if inventory_id:
            qty_col = st.columns([1])
            quantity = st.number_input(
                f"Quantity {i+1}",
                value=0.0,
                step=1.0,
                key=f"qty_{i}"
            )
        
        # Memo
        memo = st.text_input(
            f"Memo {i+1}",
            placeholder="Additional notes...",
            key=f"memo_{i}"
        )
        
        entry = {
            "account_id": account_id,
            "debit_amount": debit_amt,
            "credit_amount": credit_amt,
            "currency_code": currency,
            "exchange_rate": exchange_rate,
            "memo": memo if memo else None
        }
        
        if party_id:
            entry["party_id"] = party_id
        if inventory_id:
            entry["inventory_item_id"] = inventory_id
        if quantity:
            entry["quantity"] = quantity
        
        entries.append(entry)
        st.divider()
    
    # Balance check
    st.subheader("Balance Check")
    
    balance_col1, balance_col2, balance_col3 = st.columns(3)
    with balance_col1:
        st.metric("Total Debits (KES)", f"{total_debits:,.2f}")
    with balance_col2:
        st.metric("Total Credits (KES)", f"{total_credits:,.2f}")
    with balance_col3:
        diff = abs(total_debits - total_credits)
        if diff < 0.01:
            st.success(f"✅ Balanced!")
        else:
            st.error(f"❌ Difference: {diff:,.2f}")
    
    # Submit
    if st.button("💾 Create Transaction", type="primary", disabled=diff >= 0.01):
        try:
            payload = {
                "date": txn_date.strftime('%Y-%m-%d'),
                "description": description,
                "reference": reference if reference else None,
                "entries": entries
            }
            
            result = api.create_transaction(payload)
            
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(f"### ✅ Transaction Created!")
            st.markdown(f"**Transaction Number:** {result.get('transaction_number')}")
            st.markdown(f"**ID:** {result.get('id')}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error creating transaction: {e}")

with tab_detail:
    st.subheader("View Transaction Details")
    
    txn_id = st.text_input("Transaction ID", placeholder="Enter transaction UUID")
    
    if st.button("🔍 Load Transaction"):
        if txn_id:
            try:
                transaction = api.get_transaction(txn_id)
                
                # Header info
                st.markdown(f"### Transaction #{transaction.get('transaction_number', 'N/A')}")
                
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.write(f"**Date:** {transaction.get('date')}")
                    st.write(f"**Description:** {transaction.get('description', 'N/A')}")
                with info_col2:
                    st.write(f"**Reference:** {transaction.get('reference', 'N/A')}")
                    st.write(f"**Posted:** {'✅ Yes' if transaction.get('is_posted') else '📝 Draft'}")
                with info_col3:
                    if transaction.get('is_reversal'):
                        st.write(f"**Type:** 🔄 Reversal")
                    if transaction.get('reverses_transaction_id'):
                        st.write(f"**Reverses:** {transaction.get('reverses_transaction_id')}")
                
                # Entries table
                st.subheader("Journal Entries")
                
                if transaction.get('entries'):
                    entries_df = pd.DataFrame(transaction['entries'])
                    
                    # Format for display
                    entries_df['debit_amount'] = entries_df['debit_amount'].apply(
                        lambda x: f"{x:,.2f}" if x > 0 else ""
                    )
                    entries_df['credit_amount'] = entries_df['credit_amount'].apply(
                        lambda x: f"{x:,.2f}" if x > 0 else ""
                    )
                    entries_df['base_amount'] = entries_df['base_amount'].apply(
                        lambda x: f"KES {x:,.2f}"
                    )
                    
                    display_cols = ['account_code', 'account_name', 'debit_amount', 'credit_amount', 
                                   'currency_code', 'exchange_rate', 'base_amount', 'memo']
                    
                    st.dataframe(entries_df[[c for c in display_cols if c in entries_df.columns]], 
                                use_container_width=True, hide_index=True)
                
                # Actions
                st.subheader("Actions")
                
                if transaction.get('is_posted') and not transaction.get('is_reversal'):
                    if st.button("🔄 Reverse Transaction", type="secondary"):
                        try:
                            reversed_txn = api.reverse_transaction(txn_id)
                            st.success(f"Transaction reversed! New transaction: {reversed_txn.get('transaction_number')}")
                        except Exception as e:
                            st.error(f"Error reversing transaction: {e}")
                elif not transaction.get('is_posted'):
                    st.info("This transaction is a draft (not yet posted)")
                
            except Exception as e:
                st.error(f"Error loading transaction: {e}")
        else:
            st.warning("Please enter a transaction ID")
