"""Inventory page - Manage inventory and stock levels."""
import streamlit as st
import pandas as pd
from api_client import api

st.markdown('<p class="main-header">📦 Inventory</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Manage inventory items and track stock positions</p>', unsafe_allow_html=True)

tab_list, tab_create, tab_positions = st.tabs(["📊 View Items", "➕ Create Item", "📍 Stock Positions"])

with tab_list:
    st.subheader("All Inventory Items")
    
    try:
        items = api.get_inventory()
        
        if items:
            df = pd.DataFrame(items)
            
            # Format volatility indicator
            df['is_volatile'] = df['is_volatile'].apply(lambda x: '⚠️ Yes' if x else '✅ No')
            
            display_df = df[['name', 'sku', 'description', 'unit_type', 'is_volatile']].copy()
            display_df.columns = ['Name', 'SKU', 'Description', 'Unit', 'Volatile']
            
            # Color volatile items
            def color_volatile(val):
                if val == '⚠️ Yes':
                    return 'background-color: #fff3cd'
                return ''
            
            st.dataframe(
                display_df.style.applymap(color_volatile, subset=['Volatile']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No inventory items found")
    except Exception as e:
        st.error(f"Error loading inventory: {e}")

with tab_create:
    st.subheader("Create New Inventory Item")
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **Inventory Types:**
    - **Regular:** Standard products with stable prices
    - **Volatile:** Items with frequently changing prices (gold, forex, commodities)
    
    The system tracks average cost for inventory valuation and COGS calculation.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Item Name", placeholder="e.g., iPhone 15 Pro, 24K Gold Bar")
        sku = st.text_input("SKU", placeholder="e.g., IPHONE-15P-128GB")
        is_volatile = st.checkbox("Volatile Asset", value=False, 
                                  help="Check if price changes frequently (gold, forex, crypto)")
    
    with col2:
        unit_type = st.text_input("Unit Type", value="piece", placeholder="piece, kg, liter, meter")
        description = st.text_area("Description", placeholder="Detailed description...", height=100)
    
    if st.button("💾 Create Inventory Item", type="primary"):
        if name:
            try:
                payload = {
                    "name": name,
                    "sku": sku if sku else None,
                    "description": description if description else None,
                    "unit_type": unit_type,
                    "is_volatile": is_volatile
                }
                
                result = api.create_inventory_item(payload)
                
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown("### ✅ Inventory Item Created!")
                st.markdown(f"**Name:** {result.get('name')}")
                st.markdown(f"**SKU:** {result.get('sku') or 'N/A'}")
                st.markdown(f"**Type:** {'Volatile' if result.get('is_volatile') else 'Regular'}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error creating inventory item: {e}")
        else:
            st.warning("Please provide an item name")

with tab_positions:
    st.subheader("Current Stock Positions")
    st.markdown("*Live inventory levels with average cost calculations*")
    
    try:
        positions = api.get_inventory_positions()
        
        if positions:
            df = pd.DataFrame(positions)
            
            # Format numbers
            df['current_quantity'] = df['current_quantity'].apply(lambda x: f"{x:,.2f}")
            df['avg_cost'] = df['avg_cost'].apply(lambda x: f"KES {x:,.2f}" if x else "N/A")
            df['total_value'] = df.apply(
                lambda row: f"KES {float(row['current_quantity'].replace(',', '')) * (float(row['avg_cost'].replace('KES ', '').replace(',', '')) if row['avg_cost'] != 'N/A' else 0):,.2f}",
                axis=1
            )
            
            display_df = df[['item_name', 'item_sku', 'current_quantity', 'avg_cost', 'total_value']].copy()
            display_df.columns = ['Item', 'SKU', 'Quantity', 'Avg Cost', 'Total Value']
            
            # Highlight low stock (example threshold: < 10)
            def color_low_stock(row):
                qty = float(row['Quantity'].replace(',', ''))
                if qty <= 0:
                    return ['background-color: #f8d7da'] * len(row)
                elif qty < 10:
                    return ['background-color: #fff3cd'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                display_df.style.apply(color_low_stock, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            # Total inventory value
            total_value = sum(
                float(row['total_value'].replace('KES ', '').replace(',', ''))
                for _, row in display_df.iterrows()
            )
            
            st.divider()
            st.metric("Total Inventory Value", f"KES {total_value:,.2f}")
            
        else:
            st.info("No inventory positions found")
    except Exception as e:
        st.error(f"Error loading inventory positions: {e}")

# Quick stats
st.divider()
st.subheader("Inventory Summary")

try:
    items = api.get_inventory()
    positions = api.get_inventory_positions()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items", len(items))
    
    with col2:
        volatile_count = sum(1 for i in items if i.get('is_volatile'))
        st.metric("Volatile Items", volatile_count)
    
    with col3:
        items_with_stock = sum(1 for p in positions if p.get('current_quantity', 0) > 0)
        st.metric("Items in Stock", items_with_stock)
    
    with col4:
        out_of_stock = sum(1 for p in positions if p.get('current_quantity', 0) <= 0)
        st.metric("Out of Stock", out_of_stock)
        
except Exception:
    pass
