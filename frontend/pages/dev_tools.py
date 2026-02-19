"""Dev Tools page - Raw API access and debugging for developers."""
import streamlit as st
import requests
import json
from datetime import date
from api_client import api
import config

st.markdown('<p class="main-header">🛠️ Dev Tools</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Direct API access, debugging, and testing utilities</p>', unsafe_allow_html=True)

tab_api, tab_templates, tab_tenant, tab_raw = st.tabs([
    "🔌 API Explorer", 
    "📋 Quick Templates", 
    "🏢 Tenant Info",
    "📊 Raw Data"
])

with tab_api:
    st.subheader("API Request Builder")
    st.markdown("Make direct API calls to test endpoints")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])
        endpoint = st.text_input("Endpoint", value="accounts", placeholder="e.g., accounts, transactions, reports/trial-balance")
    
    with col2:
        body = st.text_area(
            "Request Body (JSON)",
            value='{}',
            height=150,
            placeholder='{"key": "value"}'
        )
    
    if st.button("Send Request", type="primary"):
        try:
            url = f"{config.API_BASE_URL}/{endpoint.lstrip('/')}"
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": st.session_state.get('current_tenant_id', config.DEFAULT_TENANT_ID)
            }
            
            with st.spinner("Sending request..."):
                if method == "GET":
                    response = requests.get(url, headers=headers)
                elif method == "POST":
                    data = json.loads(body) if body else {}
                    response = requests.post(url, json=data, headers=headers)
                elif method == "PUT":
                    data = json.loads(body) if body else {}
                    response = requests.put(url, json=data, headers=headers)
                else:
                    response = requests.delete(url, headers=headers)
            
            st.divider()
            
            # Request details
            with st.expander("Request Details", expanded=False):
                st.markdown("**URL:**")
                st.code(url)
                st.markdown("**Headers:**")
                st.code(json.dumps(headers, indent=2))
                if method in ["POST", "PUT"]:
                    st.markdown("**Body:**")
                    st.code(body)
            
            # Response
            st.markdown(f"**Response Status:** `{response.status_code}`")
            
            try:
                response_data = response.json()
                st.markdown("**Response Body:**")
                st.code(json.dumps(response_data, indent=2, default=str), language="json")
            except:
                st.markdown("**Response Text:**")
                st.code(response.text)
                
        except Exception as e:
            st.error(f"Error: {e}")

with tab_templates:
    st.subheader("Quick Transaction Templates")
    st.markdown("Pre-built transactions for common scenarios")
    
    template = st.selectbox(
        "Select Template",
        [
            "Simple Cash Sale (KES)",
            "Cross-Currency Import (USD)",
            "Inventory Purchase",
            "Party Payment",
            "FX Trade - Buy USD",
            "FX Trade - Sell USD",
        ]
    )
    
    templates = {
        "Simple Cash Sale (KES)": {
            "date": date.today().isoformat(),
            "description": "Cash sale",
            "reference": "SALE-001",
            "entries": [
                {
                    "account_id": "REPLACE_WITH_CASH_ACCOUNT_ID",
                    "debit_amount": 1000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0
                },
                {
                    "account_id": "REPLACE_WITH_SALES_ACCOUNT_ID",
                    "debit_amount": 0,
                    "credit_amount": 1000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0
                }
            ]
        },
        "Cross-Currency Import (USD)": {
            "date": date.today().isoformat(),
            "description": "Import from Dubai",
            "reference": "IMPORT-001",
            "entries": [
                {
                    "account_id": "REPLACE_WITH_INVENTORY_ACCOUNT_ID",
                    "debit_amount": 1000,
                    "credit_amount": 0,
                    "currency_code": "USD",
                    "exchange_rate": 130.0,
                    "memo": "Goods purchased"
                },
                {
                    "account_id": "REPLACE_WITH_PAYABLES_ACCOUNT_ID",
                    "debit_amount": 0,
                    "credit_amount": 1000,
                    "currency_code": "USD",
                    "exchange_rate": 130.0,
                    "party_id": "REPLACE_WITH_SUPPLIER_ID",
                    "memo": "Payable to supplier"
                }
            ]
        },
        "Inventory Purchase": {
            "date": date.today().isoformat(),
            "description": "Inventory purchase",
            "reference": "INV-PURCHASE-001",
            "entries": [
                {
                    "account_id": "REPLACE_WITH_INVENTORY_ACCOUNT_ID",
                    "debit_amount": 50000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "inventory_item_id": "REPLACE_WITH_ITEM_ID",
                    "quantity": 10,
                    "memo": "Stock in"
                },
                {
                    "account_id": "REPLACE_WITH_CASH_ACCOUNT_ID",
                    "debit_amount": 0,
                    "credit_amount": 50000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Payment"
                }
            ]
        },
        "Party Payment": {
            "date": date.today().isoformat(),
            "description": "Payment to supplier",
            "reference": "PAY-001",
            "entries": [
                {
                    "account_id": "REPLACE_WITH_PAYABLES_ACCOUNT_ID",
                    "debit_amount": 50000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "party_id": "REPLACE_WITH_PARTY_ID",
                    "memo": "Settlement"
                },
                {
                    "account_id": "REPLACE_WITH_CASH_ACCOUNT_ID",
                    "debit_amount": 0,
                    "credit_amount": 50000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Cash out"
                }
            ]
        },
        "FX Trade - Buy USD": {
            "date": date.today().isoformat(),
            "description": "Buy USD",
            "reference": "FX-BUY-001",
            "entries": [
                {
                    "account_id": "REPLACE_WITH_CASH_USD_ACCOUNT_ID",
                    "debit_amount": 1000,
                    "credit_amount": 0,
                    "currency_code": "USD",
                    "exchange_rate": 130.0,
                    "memo": "Buying USD"
                },
                {
                    "account_id": "REPLACE_WITH_CASH_KES_ACCOUNT_ID",
                    "debit_amount": 0,
                    "credit_amount": 130000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Selling KES"
                }
            ]
        },
        "FX Trade - Sell USD": {
            "date": date.today().isoformat(),
            "description": "Sell USD",
            "reference": "FX-SELL-001",
            "entries": [
                {
                    "account_id": "REPLACE_WITH_CASH_KES_ACCOUNT_ID",
                    "debit_amount": 132000,
                    "credit_amount": 0,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "Buying KES @ 132"
                },
                {
                    "account_id": "REPLACE_WITH_CASH_USD_ACCOUNT_ID",
                    "debit_amount": 0,
                    "credit_amount": 1000,
                    "currency_code": "USD",
                    "exchange_rate": 1.0,
                    "memo": "Selling USD"
                },
                {
                    "account_id": "REPLACE_WITH_FX_GAIN_ACCOUNT_ID",
                    "debit_amount": 0,
                    "credit_amount": 2000,
                    "currency_code": "KES",
                    "exchange_rate": 1.0,
                    "memo": "FX gain (132-130)*1000"
                }
            ]
        }
    }
    
    if template:
        st.code(json.dumps(templates[template], indent=2), language="json")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.toast("Template copied!")
        with col2:
            if st.button("🚀 Use in API Explorer"):
                st.session_state['api_template'] = templates[template]
                st.info("Switch to API Explorer tab and paste into body")

with tab_tenant:
    st.subheader("Current Tenant")
    
    current_tenant = st.session_state.get('current_tenant_id', config.DEFAULT_TENANT_ID)
    
    st.markdown("**Tenant ID:**")
    st.code(current_tenant)
    
    st.markdown("**API Base URL:**")
    st.code(config.API_BASE_URL)
    
    st.divider()
    
    st.subheader("Available Tenants (Dev Mode)")
    
    for tenant in config.DEV_TENANTS:
        is_current = tenant['id'] == current_tenant
        icon = "✅" if is_current else ""
        st.markdown(f"{icon} **{tenant['name']}**  
        ID: `{tenant['id']}`")
    
    st.divider()
    
    st.subheader("Test Tenant Connection")
    if st.button("Ping Tenant"):
        try:
            health = api.health_check()
            st.json(health)
        except Exception as e:
            st.error(f"Failed: {e}")

with tab_raw:
    st.subheader("Raw Database Views")
    st.markdown("Access raw data from database views")
    
    view = st.selectbox(
        "Select View",
        [
            "trial_balance",
            "party_balances", 
            "inventory_positions",
            "currency_exposure",
            "income_statement",
            "balance_sheet",
            "cash_flow"
        ]
    )
    
    if st.button("Fetch View Data"):
        try:
            endpoint_map = {
                "trial_balance": "reports/trial-balance",
                "party_balances": "reports/party-balances",
                "inventory_positions": "inventory/positions",
                "currency_exposure": "reports/currency-exposure",
                "income_statement": "reports/income-statement",
                "balance_sheet": "reports/balance-sheet",
                "cash_flow": "reports/cash-flow"
            }
            
            data = api._get(endpoint_map.get(view, view))
            
            st.markdown(f"**Count:** {len(data)} rows")
            st.code(json.dumps(data, indent=2, default=str), language="json")
        except Exception as e:
            st.error(f"Error fetching view: {e}")
    
    st.divider()
    
    st.subheader("API Endpoints List")
    
    endpoints = [
        ("GET", "/accounts", "List all accounts"),
        ("GET", "/accounts/{id}", "Get account by ID"),
        ("POST", "/accounts", "Create new account"),
        ("GET", "/parties", "List all parties"),
        ("GET", "/parties/{id}", "Get party by ID"),
        ("POST", "/parties", "Create new party"),
        ("GET", "/inventory", "List inventory items"),
        ("POST", "/inventory", "Create inventory item"),
        ("GET", "/inventory/positions", "Current stock levels"),
        ("GET", "/transactions", "List transactions"),
        ("GET", "/transactions/{id}", "Get transaction details"),
        ("POST", "/transactions", "Create transaction"),
        ("POST", "/transactions/{id}/reverse", "Reverse transaction"),
        ("GET", "/ledger", "Browse journal entries"),
        ("GET", "/reports/trial-balance", "Trial balance report"),
        ("GET", "/reports/income-statement", "Income statement"),
        ("GET", "/reports/balance-sheet", "Balance sheet"),
        ("GET", "/reports/cash-flow", "Cash flow"),
        ("GET", "/reports/party-balances", "Party balances"),
        ("GET", "/reports/currency-exposure", "Currency exposure"),
        ("GET", "/reports/verify-balance", "Verify ledger balance"),
    ]
    
    for method, path, desc in endpoints:
        color = {"GET": "🟢", "POST": "🔵", "PUT": "🟡", "DELETE": "🔴"}.get(method, "⚪")
        st.markdown(f"{color} **{method}** `{path}`  
        <span style='color: #666'>{desc}</span>", unsafe_allow_html=True)
