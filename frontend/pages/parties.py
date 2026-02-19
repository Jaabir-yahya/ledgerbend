"""Parties page - Manage customers, suppliers, agents."""
import streamlit as st
import pandas as pd
from api_client import api
import config

st.markdown('<p class="main-header">👥 Parties</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Manage customers, suppliers, agents, and other business relationships</p>', unsafe_allow_html=True)

tab_list, tab_create, tab_balances = st.tabs(["📊 View Parties", "➕ Create Party", "💰 Party Balances"])

with tab_list:
    st.subheader("All Parties")
    
    # Filter by type
    party_type = st.selectbox(
        "Filter by Type",
        options=["All"] + config.PARTY_TYPES,
        format_func=lambda x: x.title() if x != "All" else "All Parties"
    )
    
    try:
        parties = api.get_parties(type=party_type if party_type != "All" else None)
        
        if parties:
            df = pd.DataFrame(parties)
            
            # Format
            df['type'] = df['type'].str.title()
            
            display_df = df[['name', 'type', 'email', 'phone', 'tax_id']].copy()
            display_df.columns = ['Name', 'Type', 'Email', 'Phone', 'Tax ID']
            
            # Color by type
            def highlight_type(val):
                colors = {
                    'Customer': 'background-color: #d4edda',
                    'Supplier': 'background-color: #fff3cd',
                    'Agent': 'background-color: #d1ecf1',
                    'Runner': 'background-color: #f8d7da',
                    'Partner': 'background-color: #e2e3e5',
                    'Other': 'background-color: #f0f0f0'
                }
                return colors.get(val, '')
            
            st.dataframe(
                display_df.style.applymap(highlight_type, subset=['Type']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No parties found")
    except Exception as e:
        st.error(f"Error loading parties: {e}")

with tab_create:
    st.subheader("Create New Party")
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **Party Types:**
    - **Customer:** People or businesses who buy from you
    - **Supplier:** Vendors and businesses you buy from
    - **Agent:** People who work on your behalf
    - **Runner:** People you send with cash/items (mobile agents)
    - **Partner:** Business partners and investors
    - **Other:** Any other relationship
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Party Name", placeholder="e.g., ABC Suppliers Ltd")
        party_type = st.selectbox("Party Type", options=config.PARTY_TYPES, format_func=lambda x: x.title())
        email = st.text_input("Email", placeholder="contact@example.com")
    
    with col2:
        phone = st.text_input("Phone", placeholder="+254 700 000 000")
        tax_id = st.text_input("Tax ID", placeholder="e.g., KRA PIN")
        address = st.text_area("Address", placeholder="Physical address...", height=100)
    
    if st.button("💾 Create Party", type="primary"):
        if name and party_type:
            try:
                payload = {
                    "name": name,
                    "type": party_type,
                    "email": email if email else None,
                    "phone": phone if phone else None,
                    "tax_id": tax_id if tax_id else None,
                    "address": address if address else None
                }
                
                result = api.create_party(payload)
                
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown("### ✅ Party Created!")
                st.markdown(f"**Name:** {result.get('name')}")
                st.markdown(f"**Type:** {result.get('type')}")
                st.markdown(f"**ID:** {result.get('id')}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error creating party: {e}")
        else:
            st.warning("Please provide a name and type")

with tab_balances:
    st.subheader("Party Balances")
    st.markdown("Who owes what - outstanding balances by party")
    
    try:
        balances = api.get_party_balances()
        
        if balances:
            df = pd.DataFrame(balances)
            
            # Format amounts
            df['net_balance'] = df['net_balance'].apply(lambda x: f"KES {x:,.2f}")
            df['total_debits'] = df['total_debits'].apply(lambda x: f"KES {x:,.2f}")
            df['total_credits'] = df['total_credits'].apply(lambda x: f"KES {x:,.2f}")
            
            # Color code balances
            def color_balance(val):
                if isinstance(val, str) and val.startswith('KES'):
                    amount = float(val.replace('KES ', '').replace(',', ''))
                    if amount > 0:
                        return 'background-color: #d4edda'  # Green - they owe us
                    elif amount < 0:
                        return 'background-color: #f8d7da'  # Red - we owe them
                return ''
            
            display_df = df[['party_name', 'party_type', 'total_debits', 'total_credits', 'net_balance']].copy()
            display_df.columns = ['Party', 'Type', 'Total Debits', 'Total Credits', 'Net Balance']
            
            st.dataframe(
                display_df.style.applymap(color_balance, subset=['Net Balance']),
                use_container_width=True,
                hide_index=True
            )
            
            # Summary stats
            st.divider()
            
            total_receivable = sum(b for b in balances if b.get('net_balance', 0) > 0)
            total_payable = sum(b for b in balances if b.get('net_balance', 0) < 0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Receivables", f"KES {total_receivable:,.2f}", help="Money owed to you")
            with col2:
                st.metric("Total Payables", f"KES {abs(total_payable):,.2f}", help="Money you owe")
        else:
            st.info("No party balances found")
    except Exception as e:
        st.error(f"Error loading party balances: {e}")
