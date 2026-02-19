"""
Demo Data Initialization Script

This script populates the LedgerBend backend with realistic sample data
for testing and demonstration purposes.

Usage:
    python init_demo_data.py

Make sure the backend API is running before executing this script.
"""

import requests
import json
from datetime import date, timedelta
from typing import Dict, List
import sys
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TENANT_ID = "00000000-0000-0000-0000-000000000001"

class DemoDataLoader:
    """Loads demo data into the LedgerBend system."""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        self.created_ids = {
            'accounts': {},
            'parties': {},
            'inventory': {},
            'transactions': []
        }
    
    def _post(self, endpoint: str, data: Dict) -> Dict:
        """Make POST request to API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error posting to {endpoint}: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
    
    def _get(self, endpoint: str) -> List[Dict]:
        """Make GET request to API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting from {endpoint}: {e}")
            return []
    
    def check_api_health(self) -> bool:
        """Check if API is available."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    def create_accounts(self):
        """Create chart of accounts."""
        print("\n📊 Creating Chart of Accounts...")
        
        accounts = [
            # Assets
            {"code": "1100", "name": "Cash - KES", "type": "asset", "normal_balance": "debit"},
            {"code": "1110", "name": "Cash - USD", "type": "asset", "normal_balance": "debit"},
            {"code": "1150", "name": "M-PESA", "type": "asset", "normal_balance": "debit"},
            {"code": "1200", "name": "Bank - KES", "type": "asset", "normal_balance": "debit"},
            {"code": "1300", "name": "Inventory", "type": "asset", "normal_balance": "debit"},
            {"code": "1350", "name": "Gold Inventory", "type": "asset", "normal_balance": "debit", "is_volatile": True},
            {"code": "1400", "name": "Accounts Receivable", "type": "asset", "normal_balance": "debit"},
            
            # Liabilities
            {"code": "2100", "name": "Accounts Payable", "type": "liability", "normal_balance": "credit"},
            {"code": "2200", "name": "Partner Payables", "type": "liability", "normal_balance": "credit"},
            {"code": "2300", "name": "Bank Loan", "type": "liability", "normal_balance": "credit"},
            
            # Equity
            {"code": "3100", "name": "Owner Capital", "type": "equity", "normal_balance": "credit"},
            {"code": "3200", "name": "Retained Earnings", "type": "equity", "normal_balance": "credit"},
            
            # Income
            {"code": "4100", "name": "Sales Revenue", "type": "income", "normal_balance": "credit"},
            {"code": "4200", "name": "Service Revenue", "type": "income", "normal_balance": "credit"},
            {"code": "4500", "name": "FX Trading Gains", "type": "income", "normal_balance": "credit"},
            
            # Expenses
            {"code": "5100", "name": "Cost of Goods Sold", "type": "expense", "normal_balance": "debit"},
            {"code": "5200", "name": "Freight & Shipping", "type": "expense", "normal_balance": "debit"},
            {"code": "5300", "name": "Salaries", "type": "expense", "normal_balance": "debit"},
            {"code": "5400", "name": "Rent", "type": "expense", "normal_balance": "debit"},
            {"code": "5500", "name": "Utilities", "type": "expense", "normal_balance": "debit"},
        ]
        
        existing = self._get("accounts")
        existing_codes = {a['code'] for a in existing}
        
        for account in accounts:
            if account['code'] not in existing_codes:
                try:
                    result = self._post("accounts", account)
                    self.created_ids['accounts'][account['code']] = result['id']
                    print(f"  ✅ Created: {account['code']} - {account['name']}")
                except Exception as e:
                    print(f"  ⚠️  Skipped {account['code']}: {e}")
            else:
                print(f"  ℹ️  Already exists: {account['code']} - {account['name']}")
        
        print(f"✅ Accounts created/verified")
    
    def create_parties(self):
        """Create parties (customers, suppliers, agents)."""
        print("\n👥 Creating Parties...")
        
        parties = [
            {"name": "ABC Electronics Dubai", "type": "supplier", "email": "sales@abcdubai.com", "phone": "+971-4-1234567"},
            {"name": "Safari Phones Ltd", "type": "supplier", "email": "orders@safariphones.co.ke", "phone": "+254-20-123456"},
            {"name": "John Kamau", "type": "customer", "email": "john.kamau@email.com", "phone": "+254-712-345678"},
            {"name": "Mary Wanjiku", "type": "customer", "email": "mary.w@email.com", "phone": "+254-723-456789"},
            {"name": "Agent Peter", "type": "agent", "email": "peter@agents.co.ke", "phone": "+254-734-567890"},
            {"name": "Runner James", "type": "runner", "phone": "+254-745-678901"},
            {"name": "Partner Sarah", "type": "partner", "email": "sarah@partnership.com", "phone": "+254-756-789012"},
        ]
        
        existing = self._get("parties")
        existing_names = {p['name'] for p in existing}
        
        for party in parties:
            if party['name'] not in existing_names:
                try:
                    result = self._post("parties", party)
                    self.created_ids['parties'][party['name']] = result['id']
                    print(f"  ✅ Created: {party['name']} ({party['type']})")
                except Exception as e:
                    print(f"  ⚠️  Skipped {party['name']}: {e}")
            else:
                print(f"  ℹ️  Already exists: {party['name']}")
        
        print(f"✅ Parties created/verified")
    
    def create_inventory(self):
        """Create inventory items."""
        print("\n📦 Creating Inventory Items...")
        
        items = [
            {"name": "iPhone 15 Pro 128GB", "sku": "IP15P-128-NAT", "unit_type": "piece", "is_volatile": False},
            {"name": "iPhone 15 Pro 256GB", "sku": "IP15P-256-NAT", "unit_type": "piece", "is_volatile": False},
            {"name": "Samsung Galaxy S24", "sku": "SGS24-256", "unit_type": "piece", "is_volatile": False},
            {"name": "Screen Protector", "sku": "SCR-PROT-GEN", "unit_type": "piece", "is_volatile": False},
            {"name": "Phone Case Premium", "sku": "CASE-PREM", "unit_type": "piece", "is_volatile": False},
            {"name": "24K Gold Bar", "sku": "GOLD-24K-10G", "unit_type": "gram", "is_volatile": True},
        ]
        
        existing = self._get("inventory")
        existing_names = {i['name'] for i in existing}
        
        for item in items:
            if item['name'] not in existing_names:
                try:
                    result = self._post("inventory", item)
                    self.created_ids['inventory'][item['name']] = result['id']
                    print(f"  ✅ Created: {item['name']} ({item['unit_type']})")
                except Exception as e:
                    print(f"  ⚠️  Skipped {item['name']}: {e}")
            else:
                print(f"  ℹ️  Already exists: {item['name']}")
        
        print(f"✅ Inventory items created/verified")
    
    def get_account_id(self, code: str) -> str:
        """Get account ID by code."""
        accounts = self._get("accounts")
        for acc in accounts:
            if acc['code'] == code:
                return acc['id']
        return None
    
    def get_party_id(self, name: str) -> str:
        """Get party ID by name."""
        parties = self._get("parties")
        for party in parties:
            if party['name'] == name:
                return party['id']
        return None
    
    def get_inventory_id(self, name: str) -> str:
        """Get inventory ID by name."""
        items = self._get("inventory")
        for item in items:
            if item['name'] == name:
                return item['id']
        return None
    
    def create_transactions(self):
        """Create sample transactions."""
        print("\n💰 Creating Sample Transactions...")
        
        # Get IDs
        cash_kes = self.get_account_id("1100")
        cash_usd = self.get_account_id("1110")
        mpesa = self.get_account_id("1150")
        inventory = self.get_account_id("1300")
        gold_inv = self.get_account_id("1350")
        ar = self.get_account_id("1400")
        ap = self.get_account_id("2100")
        capital = self.get_account_id("3100")
        sales = self.get_account_id("4100")
        fx_gain = self.get_account_id("4500")
        cogs = self.get_account_id("5100")
        freight = self.get_account_id("5200")
        
        supplier_dubai = self.get_party_id("ABC Electronics Dubai")
        customer_john = self.get_party_id("John Kamau")
        
        iphone = self.get_inventory_id("iPhone 15 Pro 128GB")
        screen_prot = self.get_inventory_id("Screen Protector")
        gold = self.get_inventory_id("24K Gold Bar")
        
        if not all([cash_kes, capital]):
            print("  ⚠️  Required accounts not found. Skipping transactions.")
            return
        
        transactions = [
            # 1. Capital injection
            {
                "date": (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
                "description": "Owner capital injection",
                "reference": "CAPITAL-001",
                "entries": [
                    {"account_id": cash_kes, "debit_amount": 2000000, "credit_amount": 0, 
                     "currency_code": "KES", "exchange_rate": 1.0, "memo": "Initial capital"},
                    {"account_id": capital, "debit_amount": 0, "credit_amount": 2000000, 
                     "currency_code": "KES", "exchange_rate": 1.0, "memo": "Owner investment"}
                ]
            },
            
            # 2. Import purchase
            {
                "date": (date.today() - timedelta(days=25)).strftime('%Y-%m-%d'),
                "description": "Import iPhones from Dubai",
                "reference": "DUBAI-INV-001",
                "entries": [
                    {"account_id": inventory, "debit_amount": 15000, "credit_amount": 0, 
                     "currency_code": "USD", "exchange_rate": 130.0, 
                     "inventory_item_id": iphone, "quantity": 30, "memo": "iPhone 15 Pro x 30"},
                    {"account_id": freight, "debit_amount": 500, "credit_amount": 0, 
                     "currency_code": "USD", "exchange_rate": 130.0, "memo": "Shipping costs"},
                    {"account_id": ap, "debit_amount": 0, "credit_amount": 15500, 
                     "currency_code": "USD", "exchange_rate": 130.0, 
                     "party_id": supplier_dubai, "memo": "Payable to Dubai supplier"}
                ]
            },
            
            # 3. Cash sale
            {
                "date": (date.today() - timedelta(days=20)).strftime('%Y-%m-%d'),
                "description": "Cash sale - iPhone to John Kamau",
                "reference": "SALE-001",
                "entries": [
                    {"account_id": cash_kes, "debit_amount": 180000, "credit_amount": 0, 
                     "currency_code": "KES", "exchange_rate": 1.0, "memo": "Cash received"},
                    {"account_id": sales, "debit_amount": 0, "credit_amount": 180000, 
                     "currency_code": "KES", "exchange_rate": 1.0, "memo": "iPhone sale"},
                    {"account_id": cogs, "debit_amount": 130000, "credit_amount": 0, 
                     "currency_code": "KES", "exchange_rate": 1.0, 
                     "inventory_item_id": iphone, "quantity": -1, "memo": "COGS"},
                    {"account_id": inventory, "debit_amount": 0, "credit_amount": 130000, 
                     "currency_code": "KES", "exchange_rate": 1.0, 
                     "inventory_item_id": iphone, "quantity": -1, "memo": "Stock out"}
                ]
            },
            
            # 4. M-PESA sale
            {
                "date": (date.today() - timedelta(days=15)).strftime('%Y-%m-%d'),
                "description": "M-PESA sale - accessories",
                "reference": "MPESA-QW12E34",
                "entries": [
                    {"account_id": mpesa, "debit_amount": 5000, "credit_amount": 0, 
                     "currency_code": "KES", "exchange_rate": 1.0, "memo": "M-PESA payment"},
                    {"account_id": sales, "debit_amount": 0, "credit_amount": 5000, 
                     "currency_code": "KES", "exchange_rate": 1.0, "memo": "Accessories sale"}
                ]
            },
            
            # 5. Buy USD
            {
                "date": (date.today() - timedelta(days=10)).strftime('%Y-%m-%d'),
                "description": "Buy USD for FX trading",
                "reference": "FX-BUY-001",
                "entries": [
                    {"account_id": cash_usd, "debit_amount": 5000, "credit_amount": 0, 
                     "currency_code": "USD", "exchange_rate": 130.0, "memo": "Buying USD"},
                    {"account_id": cash_kes, "debit_amount": 0, "credit_amount": 650000, 
                     "currency_code": "KES", "exchange_rate": 1.0, "memo": "KES paid"}
                ]
            },
        ]
        
        for txn in transactions:
            try:
                result = self._post("transactions", txn)
                self.created_ids['transactions'].append(result['id'])
                print(f"  ✅ Created: {txn['description'][:40]}...")
            except Exception as e:
                print(f"  ⚠️  Failed to create transaction: {e}")
        
        print(f"✅ Created {len(self.created_ids['transactions'])} transactions")
    
    def run(self):
        """Execute full demo data load."""
        print("=" * 60)
        print("🚀 LedgerBend Demo Data Initialization")
        print("=" * 60)
        
        # Check API health
        print("\n🔍 Checking API health...")
        if not self.check_api_health():
            print("❌ API is not responding!")
            print(f"   Please ensure backend is running at {API_BASE_URL}")
            sys.exit(1)
        print("✅ API is healthy")
        
        try:
            # Create data
            self.create_accounts()
            self.create_parties()
            self.create_inventory()
            self.create_transactions()
            
            print("\n" + "=" * 60)
            print("✅ Demo data initialization complete!")
            print("=" * 60)
            print("\n📊 Summary:")
            print(f"   - Accounts: {len(self.created_ids['accounts'])} created")
            print(f"   - Parties: {len(self.created_ids['parties'])} created")
            print(f"   - Inventory: {len(self.created_ids['inventory'])} created")
            print(f"   - Transactions: {len(self.created_ids['transactions'])} created")
            print("\n🌐 You can now open the Streamlit frontend and explore!")
            print("   Run: streamlit run app.py")
            
        except Exception as e:
            print(f"\n❌ Error during initialization: {e}")
            sys.exit(1)

if __name__ == "__main__":
    loader = DemoDataLoader()
    loader.run()
