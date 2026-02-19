# LedgerBend Streamlit Frontend

A production-ready reference frontend for the LedgerBend Universal Double-Entry Ledger API.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start the Backend

Make sure your LedgerBend FastAPI backend is running:

```bash
# In the root directory
python main.py
# or
uvicorn main:app --reload --port 8000
```

### 4. Launch the Frontend

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📋 Features

### Dashboard
- Real-time financial health overview
- Key metrics (accounts, parties, inventory, transactions)
- Balance verification status
- Quick action shortcuts

### Transactions
- Create complex multi-entry transactions
- Support for multiple currencies and exchange rates
- Inventory tracking with quantity
- Party linking (customers, suppliers, agents)
- View and reverse transactions
- Real-time balance validation

### Ledger
- Browse all journal entries
- Advanced filtering by account, party, inventory, currency, date
- Export to CSV
- Quick filter shortcuts

### Accounts
- Full chart of accounts management
- Account creation with type and normal balance
- Color-coded by account type
- Summary statistics

### Parties
- Manage customers, suppliers, agents, runners
- Party type categorization
- Balance tracking per party
- Contact information management

### Inventory
- Inventory item management
- Stock position tracking with average cost
- Volatile asset flagging (gold, forex)
- Inventory valuation

### Reports
- **Trial Balance:** Verify debits = credits
- **Income Statement:** P&L with visualizations
- **Balance Sheet:** Assets, liabilities, equity
- **Cash Flow:** Operating cash movements
- **Currency Exposure:** FX positions
- Date range filtering
- Interactive charts

### Use Cases
- Import business workflows
- Retail sales scenarios
- Forex trading examples
- Gold trading and revaluation
- Runner/field agent tracking
- Correction and reversal workflows
- Month-end close process
- Advanced multi-party transactions

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
# API Configuration
API_BASE_URL=http://localhost:8000/api/v1

# Default tenant (for single-tenant mode)
DEFAULT_TENANT_ID=00000000-0000-0000-0000-000000000001

# Demo Mode
DEMO_MODE=false
```

### API Endpoints Used

The frontend integrates with these LedgerBend API endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/accounts` | List accounts |
| POST | `/accounts` | Create account |
| GET | `/parties` | List parties |
| POST | `/parties` | Create party |
| GET | `/inventory` | List inventory |
| POST | `/inventory` | Create inventory item |
| GET | `/inventory/positions` | Stock levels |
| GET | `/transactions` | List transactions |
| GET | `/transactions/{id}` | Get transaction |
| POST | `/transactions` | Create transaction |
| POST | `/transactions/{id}/reverse` | Reverse transaction |
| GET | `/ledger` | Browse entries |
| GET | `/reports/verify-balance` | Balance check |
| GET | `/reports/trial-balance` | Trial balance |
| GET | `/reports/income-statement` | P&L report |
| GET | `/reports/balance-sheet` | Balance sheet |
| GET | `/reports/cash-flow` | Cash flow |
| GET | `/reports/party-balances` | Party balances |
| GET | `/reports/currency-exposure` | FX positions |

## 📊 Demo Mode

Enable demo mode to populate the system with sample data:

```bash
# Set in .env
DEMO_MODE=true

# Or run the demo script
python init_demo_data.py
```

This creates:
- Sample chart of accounts
- Test parties (customers, suppliers, agents)
- Inventory items
- Realistic transactions covering all use cases

## 🎯 For Frontend Developers

### Architecture Overview

```
frontend/
├── app.py                 # Main entry point, navigation
├── config.py             # Configuration constants
├── api_client.py         # API wrapper class
├── requirements.txt      # Dependencies
├── .env.example         # Environment template
├── pages/
│   ├── dashboard.py     # Overview dashboard
│   ├── transactions.py  # Transaction CRUD
│   ├── ledger.py        # Journal entry browser
│   ├── accounts.py      # Chart of accounts
│   ├── parties.py       # Party management
│   ├── inventory.py     # Inventory tracking
│   ├── reports.py       # Financial reports
│   └── use_cases.py     # Business scenarios
└── README.md
```

### Key Components

#### API Client (`api_client.py`)
Centralized API communication with error handling:

```python
from api_client import api

# Example usage
transactions = api.get_transactions(limit=10)
accounts = api.get_accounts(type='asset')
```

#### Configuration (`config.py`)
All constants and enums in one place:
- Account types
- Party types  
- Currencies
- Display formats

### State Management

Streamlit's session state is used for:
- API connection status
- User selections
- Cached data
- Filter states

### Styling

Custom CSS in `app.py` provides:
- Consistent color scheme
- Card layouts
- Status indicators (success, warning, error)
- Responsive tables

## 🧪 Testing

### Manual Testing Checklist

- [ ] API connection shows "Connected"
- [ ] Can create an account
- [ ] Can create a party
- [ ] Can create inventory item
- [ ] Can create transaction with multiple entries
- [ ] Balance validation works (debits must = credits)
- [ ] Can view transaction details
- [ ] Can reverse a transaction
- [ ] Ledger filters work
- [ ] All reports load correctly
- [ ] Currency exposure shows FX positions
- [ ] Use case examples are clear

### API Testing

Test backend connectivity:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🐛 Troubleshooting

### "Cannot connect to API"
- Check backend is running on correct port
- Verify `API_BASE_URL` in `.env`
- Check firewall/network settings

### "Import errors"
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Use Python 3.8+

### "Transaction balance error"
- Verify total debits equal total credits
- Check exchange rates are correct
- Ensure each entry has debit OR credit, not both

### "Page not loading"
- Clear browser cache
- Check browser console for JavaScript errors
- Restart Streamlit: `Ctrl+C` then `streamlit run app.py`

## 📝 Data Model Reference

### Account
```python
{
  "id": "uuid",
  "code": "1100",
  "name": "Cash KES",
  "type": "asset",  # asset, liability, equity, income, expense
  "normal_balance": "debit",  # debit or credit
  "is_active": true
}
```

### Party
```python
{
  "id": "uuid",
  "name": "ABC Suppliers",
  "type": "supplier",  # customer, supplier, agent, runner, partner, other
  "email": "contact@abc.com",
  "phone": "+254...",
  "tax_id": "KRA123..."
}
```

### Inventory Item
```python
{
  "id": "uuid",
  "name": "iPhone 15 Pro",
  "sku": "IP15P-128",
  "unit_type": "piece",
  "is_volatile": false  # true for gold, forex, etc.
}
```

### Transaction
```python
{
  "id": "uuid",
  "transaction_number": "TXN-2024-001",
  "date": "2024-01-15",
  "description": "Purchase from Dubai",
  "reference": "INV-001",
  "is_posted": true,
  "is_reversal": false,
  "entries": [...]
}
```

### Journal Entry
```python
{
  "account_id": "uuid",
  "debit_amount": 100000,
  "credit_amount": 0,
  "currency_code": "KES",
  "exchange_rate": 1.0,
  "party_id": "uuid",  # optional
  "inventory_item_id": "uuid",  # optional
  "quantity": 10,  # optional
  "memo": "Additional notes"
}
```

## 🎨 Customization

### Adding New Currencies
Edit `config.py`:
```python
CURRENCIES = ["KES", "USD", "EUR", "GBP", "UGX", "TZS", "NEW_CURR"]
```

### Changing Date Format
Edit `config.py`:
```python
DATE_FORMAT = "%Y-%m-%d"  # ISO format
# or
DATE_FORMAT = "%d/%m/%Y"  # UK format
```

### Custom Styling
Modify CSS in `app.py` under the `st.markdown` block.

## 🤝 Contributing

This is a reference implementation for the frontend team. To suggest improvements:

1. Test the current implementation
2. Identify gaps or improvements
3. Discuss with the team
4. Update documentation

## 📄 License

Part of the LedgerBend Universal Double-Entry Ledger project.

## 🔗 Resources

- Backend API Docs: `http://localhost:8000/docs` (when backend running)
- Streamlit Docs: https://docs.streamlit.io
- FastAPI Docs: https://fastapi.tiangolo.com

---

**Built for Phase 1: The Truth Layer**  
*Log any financial mess accurately now. Unlock infinite reporting possibilities later.*
