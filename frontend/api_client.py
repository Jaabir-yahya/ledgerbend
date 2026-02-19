"""API client for LedgerBend backend."""
import requests
from typing import Optional, Dict, Any, List
import config
import streamlit as st

class APIClient:
    """Client for interacting with the LedgerBend API."""
    
    def __init__(self, base_url: str = None, tenant_id: str = None):
        self.base_url = base_url or config.API_BASE_URL
        self.tenant_id = tenant_id or config.DEFAULT_TENANT_ID
        self.session = requests.Session()
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with current tenant."""
        # Get tenant from session state if available (for dev mode switching)
        try:
            current_tenant = st.session_state.get('current_tenant_id', self.tenant_id)
        except:
            current_tenant = self.tenant_id
        
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tenant-ID": current_tenant
        })
    
    def _url(self, path: str) -> str:
        """Build full URL from path."""
        # Update headers before each request to pick up tenant changes
        self._update_headers()
        return f"{self.base_url}/{path.lstrip('/')}"
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        try:
            response = self.session.get(self._url("health"))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Accounts
    def get_accounts(self, type: str = None) -> List[Dict]:
        """Get all accounts, optionally filtered by type."""
        params = {}
        if type:
            params["type"] = type
        response = self.session.get(self._url("accounts"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_account(self, account_id: str) -> Dict:
        """Get a specific account."""
        response = self.session.get(self._url(f"accounts/{account_id}"))
        response.raise_for_status()
        return response.json()
    
    def create_account(self, data: Dict) -> Dict:
        """Create a new account."""
        response = self.session.post(self._url("accounts"), json=data)
        response.raise_for_status()
        return response.json()
    
    # Parties
    def get_parties(self, type: str = None) -> List[Dict]:
        """Get all parties, optionally filtered by type."""
        params = {}
        if type:
            params["type"] = type
        response = self.session.get(self._url("parties"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_party(self, party_id: str) -> Dict:
        """Get a specific party."""
        response = self.session.get(self._url(f"parties/{party_id}"))
        response.raise_for_status()
        return response.json()
    
    def create_party(self, data: Dict) -> Dict:
        """Create a new party."""
        response = self.session.post(self._url("parties"), json=data)
        response.raise_for_status()
        return response.json()
    
    # Inventory
    def get_inventory(self) -> List[Dict]:
        """Get all inventory items."""
        response = self.session.get(self._url("inventory"))
        response.raise_for_status()
        return response.json()
    
    def get_inventory_positions(self) -> List[Dict]:
        """Get current inventory positions."""
        response = self.session.get(self._url("inventory/positions"))
        response.raise_for_status()
        return response.json()
    
    def create_inventory_item(self, data: Dict) -> Dict:
        """Create a new inventory item."""
        response = self.session.post(self._url("inventory"), json=data)
        response.raise_for_status()
        return response.json()
    
    # Transactions
    def get_transactions(
        self, 
        start_date: str = None, 
        end_date: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """Get transactions with optional date filters."""
        params = {"limit": limit, "offset": offset}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        response = self.session.get(self._url("transactions"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_transaction(self, transaction_id: str) -> Dict:
        """Get a specific transaction with entries."""
        response = self.session.get(self._url(f"transactions/{transaction_id}"))
        response.raise_for_status()
        return response.json()
    
    def create_transaction(self, data: Dict) -> Dict:
        """Create and post a transaction."""
        response = self.session.post(self._url("transactions"), json=data)
        response.raise_for_status()
        return response.json()
    
    def reverse_transaction(self, transaction_id: str) -> Dict:
        """Reverse a posted transaction."""
        response = self.session.post(self._url(f"transactions/{transaction_id}/reverse"))
        response.raise_for_status()
        return response.json()
    
    # Ledger
    def get_ledger(
        self,
        account_id: str = None,
        party_id: str = None,
        inventory_item_id: str = None,
        currency_code: str = None,
        start_date: str = None,
        end_date: str = None,
        tags: List[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Browse ledger entries with filters."""
        params = {"limit": limit, "offset": offset}
        if account_id:
            params["account_id"] = account_id
        if party_id:
            params["party_id"] = party_id
        if inventory_item_id:
            params["inventory_item_id"] = inventory_item_id
        if currency_code:
            params["currency_code"] = currency_code
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if tags:
            params["tags"] = ",".join(tags)
        
        response = self.session.get(self._url("ledger"), params=params)
        response.raise_for_status()
        return response.json()
    
    # Reports
    def get_trial_balance(self) -> List[Dict]:
        """Get trial balance report."""
        response = self.session.get(self._url("reports/trial-balance"))
        response.raise_for_status()
        return response.json()
    
    def get_income_statement(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get income statement (P&L)."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        response = self.session.get(self._url("reports/income-statement"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_income_statement_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get income statement summary."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        response = self.session.get(self._url("reports/income-statement/summary"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_balance_sheet(self, date_to: str = None) -> Dict:
        """Get balance sheet."""
        params = {}
        if date_to:
            params["date_to"] = date_to
        response = self.session.get(self._url("reports/balance-sheet"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_balance_sheet_summary(self, date_to: str = None) -> Dict:
        """Get balance sheet summary."""
        params = {}
        if date_to:
            params["date_to"] = date_to
        response = self.session.get(self._url("reports/balance-sheet/summary"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_cash_flow(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get cash flow statement."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        response = self.session.get(self._url("reports/cash-flow"), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_party_balances(self) -> List[Dict]:
        """Get party balances."""
        response = self.session.get(self._url("reports/party-balances"))
        response.raise_for_status()
        return response.json()
    
    def get_currency_exposure(self) -> List[Dict]:
        """Get currency exposure report."""
        response = self.session.get(self._url("reports/currency-exposure"))
        response.raise_for_status()
        return response.json()
    
    def verify_balance(self) -> Dict:
        """Verify ledger balance (golden rule check)."""
        response = self.session.get(self._url("reports/verify-balance"))
        response.raise_for_status()
        return response.json()

# Global client instance
api = APIClient()
