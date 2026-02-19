# Testing Guide

## Manual Testing Procedures

### 1. Setup Verification

```bash
cd frontend
python verify_setup.py
```

Expected output: All checks should pass

### 2. API Connectivity

```bash
curl http://localhost:8000/api/v1/health
```

Expected: `{"status": "ok"}`

### 3. Page Load Tests

Test each page loads without errors:
- [ ] Dashboard
- [ ] Transactions
- [ ] Ledger
- [ ] Accounts
- [ ] Parties
- [ ] Inventory
- [ ] Reports
- [ ] Use Cases

### 4. Transaction Creation Flow

**Test Case: Simple Cash Sale**
1. Go to Transactions page
2. Click "Create Transaction"
3. Fill:
   - Date: Today
   - Description: "Test sale"
   - Entry 1: Cash KES, Debit, 1000
   - Entry 2: Sales, Credit, 1000
4. Submit
5. Verify success message
6. Check transaction appears in list

**Test Case: Cross-Currency Import**
1. Create transaction with USD amounts
2. Verify exchange rate field
3. Submit
4. Check base amounts calculated correctly

### 5. Tenant Switching

1. Select different tenant from sidebar
2. Verify page refreshes
3. Verify data changes (if tenants have different data)
4. Check X-Tenant-ID header in browser dev tools

### 6. Report Generation

1. Go to Reports page
2. Select date range
3. Verify all reports load:
   - Trial Balance
   - Income Statement
   - Balance Sheet
   - Cash Flow
   - Currency Exposure

### 7. Error Handling

**Test Case: Invalid Transaction**
1. Try to create unbalanced transaction
2. Verify error message shows
3. Verify form stays populated

**Test Case: Backend Down**
1. Stop backend
2. Try to load page
3. Verify graceful error message
4. Start backend
5. Verify recovery works

## API Testing Examples

### Create Account
```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -d '{
    "code": "9999",
    "name": "Test Account",
    "type": "asset",
    "normal_balance": "debit"
  }'
```

### Create Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -d '{
    "date": "2024-01-15",
    "description": "Test transaction",
    "entries": [
      {
        "account_id": "1100",
        "debit_amount": 1000,
        "credit_amount": 0,
        "currency_code": "KES",
        "exchange_rate": 1.0
      },
      {
        "account_id": "4100",
        "debit_amount": 0,
        "credit_amount": 1000,
        "currency_code": "KES",
        "exchange_rate": 1.0
      }
    ]
  }'
```

### Verify Balance
```bash
curl http://localhost:8000/api/v1/reports/verify-balance \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

## Automated Testing Ideas

Future enhancements:
- Unit tests for API client
- Integration tests with mock backend
- Visual regression tests
- Performance benchmarks
- Accessibility tests

## Known Limitations

1. **Large Datasets:** Tables with >1000 rows may be slow
2. **Mobile:** Some complex forms need scrolling
3. **File Uploads:** Not yet implemented
4. **Offline Mode:** Not supported
5. **Real-time Updates:** Manual refresh required

## Debugging Tips

### View API Calls
Open browser DevTools → Network tab → Filter by "api"

### Check Tenant Header
In Network tab, click any request → Headers → Request Headers → X-Tenant-ID

### Streamlit Debug Mode
```bash
streamlit run app.py --logger.level debug
```

### Backend Logs
Watch backend terminal for API errors

### Common Issues

**"Cannot connect to API"**
- Backend not running
- Wrong API_BASE_URL in .env
- CORS not configured

**"Import errors"**
- Run: `pip install -r requirements.txt`
- Check Python version (3.8+)

**"Page not found"**
- File must be in `pages/` directory
- Filename must end in `.py`
- Must be imported in `app.py` navigation
