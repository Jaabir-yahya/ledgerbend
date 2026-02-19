"""Configuration for the Streamlit frontend."""
import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Default tenant (for single-tenant mode)
DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "00000000-0000-0000-0000-000000000001")

# Dev Mode: Available tenants for switching
# In production, this would come from an API endpoint
DEV_TENANTS = [
    {"id": "00000000-0000-0000-0000-000000000001", "name": "🧪 Test Tenant 1"},
    {"id": "00000000-0000-0000-0000-000000000002", "name": "🏪 Acme Corp"},
    {"id": "00000000-0000-0000-0000-000000000003", "name": "🚢 Import Biz"},
    {"id": "00000000-0000-0000-0000-000000000004", "name": "💱 Forex Bureau"},
    {"id": "00000000-0000-0000-0000-000000000005", "name": "🏃 Logistics Co"},
]

# UI Configuration
PAGE_TITLE = "LedgerBend - Universal Double-Entry Ledger"
PAGE_ICON = "📊"

# Chart of Account Types
ACCOUNT_TYPES = ["asset", "liability", "equity", "income", "expense"]

# Party Types
PARTY_TYPES = ["customer", "supplier", "agent", "runner", "partner", "other"]

# Common Currencies
CURRENCIES = ["KES", "USD", "EUR", "GBP", "UGX", "TZS"]

# Date format for display
DATE_FORMAT = "%Y-%m-%d"

# Pagination
DEFAULT_PAGE_SIZE = 20
