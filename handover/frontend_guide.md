# Frontend Handover Guide: Universal Ledger

The backend is a **Double-Entry Truth Layer**. It enforces accounting rules strictly so the frontend doesn't have to.

## Core Concepts for Frontend
1. **The Transaction is the Unit**: You never post a single entry. You post a `Transaction` containing 2 or more `Entries`.
2. **Base Currency (KES)**: The ledger calculates everything in KES internally. When posting in other currencies (USD, GBP), you **must** provide an `exchange_rate`.
3. **Immutability**: Once a transaction is posted, it cannot be edited or deleted. To "fix" a mistake, use the `/reverse` endpoint, then post a new corrected transaction.
4. **Tenant ID**: Every request needs a `tenant_id`. Use `00000000-0000-0000-0000-000000000001` for the default setup.

## Key API Flows

### 1. Simple Cash Movement (M-PESA to Bank)
```javascript
const response = await fetch('/api/v1/transactions', {
  method: 'POST',
  body: JSON.stringify({
    tenant_id: "00000000-0000-0000-0000-000000000001",
    date: "2024-03-20",
    description: "Transfer from M-PESA to Bank",
    entries: [
      {
        account_id: "...", // M-PESA account UUID
        credit_amount: 5000,
        currency_code: "KES",
        exchange_rate: 1
      },
      {
        account_id: "...", // Bank account UUID
        debit_amount: 5000,
        currency_code: "KES",
        exchange_rate: 1
      }
    ]
  })
});
```

### 2. Inventory Purchase (Cross-Currency)
When buying goods in USD but tracking inventory in KES:
- **Debit** Inventory (Amount in KES, rate = 1)
- **Credit** Bank USD (Amount in USD, rate = current exchange rate)
- The system validates that `Inventory_KES * 1 == Bank_USD * Rate`.

### 3. Reversing a Mistake
```javascript
// POST /api/v1/transactions/{id}/reverse
{
  "date": "2024-03-21",
  "description": "Correcting error in yesterday's entry"
}
```

## Useful Reports for UI
- `GET /api/v1/reports/trial-balance`: Use this for the "Dashboard" overview.
- `GET /api/v1/reports/party-balances`: Use this for "Customer/Supplier" statements.
- `GET /api/v1/inventory/positions`: Use this for "Stock Levels".
- `GET /api/v1/reports/verify-balance`: Show a "System Health" green tick if this returns `is_balanced: true`.

## Advanced Use Cases

### 1. On-behalf-of Payment
When you pay a supplier on behalf of a partner (partner will owe you KES):
- **Debit** Accounts Receivable (Partner ID)
- **Credit** Bank/Cash
- *Result:* Partner's balance increases in your favor.

### 2. Mark-to-Market Revaluation (Volatile Assets)
When gold price goes up and you want to reflect the gain without changing quantity:
- **Debit** Inventory (Gold) - *Amount = Value Increase, Rate = 1, Qty = 0*
- **Credit** Unrealized Gain (Income)
- *Note:* Our DB allows quantity to be NULL if it's just a value adjustment.

### 3. Forex Trading
Buying USD @ 128, selling @ 132:
- **Buy:** Debit USD Bank (Rate 128), Credit KES Bank (Rate 1).
- **Sell:** Debit KES Bank (Rate 1), Credit USD Bank (Rate 132).
- The "Profit" automatically accumulates in the KES account net balance.

## Production Checklist
1. **CORS**: Set `CORS_ORIGINS` env var to your frontend domain (e.g. `https://myapp.vercel.app`).
2. **Tenant ID**: Ensure your frontend always stores and sends the correct `tenant_id` for the user.
3. **Rounding**: The backend rounds to 4 decimal places. Ensure your UI displays at least 2 decimals for currency.

## Typescript Snippet (Quick Start)
```typescript
interface JournalEntry {
  account_id: string;
  debit_amount?: number;
  credit_amount?: number;
  currency_code: string;
  exchange_rate: number;
  party_id?: string;
  inventory_item_id?: string;
  quantity?: number;
  memo?: string;
  tags?: string[];
}

interface Transaction {
  tenant_id: string;
  date: string;
  description: string;
  entries: JournalEntry[];
}
```
