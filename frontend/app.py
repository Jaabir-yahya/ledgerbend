"""Main Streamlit application for LedgerBend."""
import streamlit as st
import config

# Page config
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'current_tenant_id' not in st.session_state:
    st.session_state.current_tenant_id = config.DEFAULT_TENANT_ID

# Sidebar navigation
st.sidebar.markdown(f"# {config.PAGE_ICON} LedgerBend")
st.sidebar.markdown("*Universal Double-Entry Ledger*")

# DEV MODE: Tenant Switcher
st.sidebar.divider()
st.sidebar.markdown("### 🏢 Tenant (Dev Mode)")

tenant_options = {t['name']: t['id'] for t in config.DEV_TENANTS}
selected_tenant_name = st.sidebar.selectbox(
    "Switch Tenant",
    options=list(tenant_options.keys()),
    index=list(tenant_options.values()).index(st.session_state.current_tenant_id) if st.session_state.current_tenant_id in tenant_options.values() else 0,
    key="tenant_selector"
)

new_tenant_id = tenant_options[selected_tenant_name]
if new_tenant_id != st.session_state.current_tenant_id:
    st.session_state.current_tenant_id = new_tenant_id
    st.sidebar.success(f"✅ Switched to {selected_tenant_name}")
    st.rerun()

st.sidebar.caption(f"**Current:** `{st.session_state.current_tenant_id[:8]}...`")
st.sidebar.divider()

# Navigation
pages = {
    "📊 Dashboard": "pages/dashboard.py",
    "💰 Transactions": "pages/transactions.py",
    "📒 Ledger": "pages/ledger.py",
    "📋 Accounts": "pages/accounts.py",
    "👥 Parties": "pages/parties.py",
    "📦 Inventory": "pages/inventory.py",
    "📈 Reports": "pages/reports.py",
    "🎯 Use Cases": "pages/use_cases.py",
    "🛠️ Dev Tools": "pages/dev_tools.py",
}

selection = st.sidebar.radio("Navigation", list(pages.keys()))

# API Status in sidebar
st.sidebar.divider()
with st.sidebar.expander("🔌 API Connection"):
    from api_client import api
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Test", use_container_width=True):
            try:
                health = api.health_check()
                if health.get("status") == "ok":
                    st.session_state.api_connected = True
                    st.success("Connected!")
                else:
                    st.session_state.api_connected = False
                    st.error("Failed")
            except Exception as e:
                st.session_state.api_connected = False
                st.error(f"Error: {e}")
    
    with col2:
        st.markdown(f"**URL:** `{config.API_BASE_URL}`")
    
    if st.session_state.api_connected:
        st.success("✅ API Connected")
    else:
        st.warning("⚠️ Not connected")

# Footer
st.sidebar.divider()
st.sidebar.caption("v1.0.0 | Reference Frontend")

# Run selected page
page_file = pages[selection]
exec(open(page_file).read())
