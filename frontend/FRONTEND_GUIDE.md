# FRONTEND TEAM - INTEGRATION GUIDE

## 🎯 Quick Reference for Frontend Developers

### API Integration

The `api_client.py` provides a centralized API wrapper:

```python
from api_client import api

# Get data
accounts = api.get_accounts()
transactions = api.get_transactions(limit=10)

# Create data
new_account = api.create_account({
    "code": "1100",
    "name": "Cash",
    "type": "asset",
    "normal_balance": "debit"
})
```

### Page Structure Template

Each page follows this structure:

```python
"""Page description."""
import streamlit as st
import pandas as pd
from api_client import api
from components import show_error, show_success, loading_spinner

st.markdown('<p class="main-header">📊 Page Title</p>', unsafe_allow_html=True)

# Main content
with loading_spinner("Loading..."):
    try:
        data = api.get_data()
        st.dataframe(data)
    except Exception as e:
        show_error("Failed to load data", str(e))
```

### Adding a New Page

1. Create file in `pages/` directory (e.g., `pages/new_feature.py`)
2. Add to navigation in `app.py`:
   ```python
   pages = {
       "📊 Dashboard": "pages/dashboard.py",
       "🆕 New Feature": "pages/new_feature.py",  # Add here
   }
   ```
3. Run and test

### Common Components

From `components.py`:

```python
from components import (
    show_error,      # Display error with details
    show_success,    # Display success message
    show_warning,    # Display warning
    show_info,       # Display info box
    loading_spinner, # Show loading spinner
    empty_state,     # Empty state placeholder
    metric_card,     # Styled metric card
    section_header,  # Section header with description
)
```

### Form Patterns

**Creating a New Item:**

```python
with st.form("create_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    
    submitted = st.form_submit_button("Create")
    if submitted:
        try:
            result = api.create_item({
                "name": name,
                "email": email
            })
            show_success(f"Created: {result['name']}")
            st.rerun()
        except Exception as e:
            show_error("Create failed", str(e))
```

**Transaction Entry Builder:**

```python
# Dynamic entries
num_entries = st.number_input("Entries", min_value=2, max_value=10, value=2)
entries = []

for i in range(int(num_entries)):
    cols = st.columns([2, 1, 1])
    with cols[0]:
        account = st.selectbox(f"Account {i+1}", account_options, key=f"acct_{i}")
    with cols[1]:
        entry_type = st.selectbox(f"Type {i+1}", ["debit", "credit"], key=f"type_{i}")
    with cols[2]:
        amount = st.number_input(f"Amount {i+1}", key=f"amt_{i}")
    
    entries.append({
        "account_id": account,
        "debit_amount": amount if entry_type == "debit" else 0,
        "credit_amount": amount if entry_type == "credit" else 0,
        "currency_code": "KES",
        "exchange_rate": 1.0
    })

# Balance check
total_debits = sum(e['debit_amount'] for e in entries)
total_credits = sum(e['credit_amount'] for e in entries)
is_balanced = abs(total_debits - total_credits) < 0.01
```

### Data Tables

**Basic Table:**
```python
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True, hide_index=True)
```

**Styled Table:**
```python
def color_type(val):
    colors = {
        'asset': 'background-color: #d4edda',
        'liability': 'background-color: #f8d7da',
    }
    return colors.get(val, '')

st.dataframe(
    df.style.applymap(color_type, subset=['type']),
    use_container_width=True
)
```

**With Actions:**
```python
col1, col2 = st.columns([3, 1])
with col1:
    st.dataframe(df)
with col2:
    if st.button("Edit", key=f"edit_{row_id}"):
        st.session_state['edit_id'] = row_id
        st.rerun()
```

### Session State Usage

```python
# Initialize
if 'selected_transaction' not in st.session_state:
    st.session_state.selected_transaction = None

# Set
st.session_state.selected_transaction = txn_id

# Get
current = st.session_state.get('selected_transaction')
```

### API Response Handling

**Success Pattern:**
```python
try:
    result = api.create_transaction(data)
    show_success(f"Created transaction {result['transaction_number']}")
    st.rerun()  # Refresh page
except requests.exceptions.HTTPError as e:
    error_detail = e.response.json() if e.response else {}
    show_error(
        "Transaction failed",
        error_detail.get('detail', str(e))
    )
```

**Error Handling:**
```python
from components import api_call_with_loading

result = api_call_with_loading(
    api.create_transaction,
    data,
    loading_text="Creating transaction...",
    error_prefix="Failed to create transaction"
)

if result:
    show_success("Created!")
```

### Testing Checklist

When adding a new feature:

- [ ] API endpoint works via curl/Postman
- [ ] Page loads without errors
- [ ] Form validation works
- [ ] Success case works
- [ ] Error case displays properly
- [ ] Loading states shown
- [ ] Works with empty data
- [ ] Works with large datasets
- [ ] Responsive on different screen sizes
- [ ] Tenant switching works

### Common Gotchas

1. **Streamlit reruns on every interaction** - Use session state to persist data
2. **API calls are synchronous** - Use loading spinners for UX
3. **DataFrame columns must match exactly** - Check column names
4. **Streamlit selectbox needs unique keys** - Always provide key parameter
5. **Exchange rates multiply amounts** - Base amount = amount * rate
6. **Tenant switching requires header** - API client handles this automatically

### CSS Classes Available

From `app.py`:
- `.main-header` - Page title
- `.sub-header` - Page description
- `.metric-card` - Metric container
- `.success-box` - Green message box
- `.warning-box` - Yellow message box
- `.error-box` - Red message box
- `.info-box` - Blue message box

Example:
```python
st.markdown('<div class="success-box">Success!</div>', unsafe_allow_html=True)
```

### Backend API Docs

When backend is running, view interactive docs at:
```
http://localhost:8000/docs
```

### Getting Help

1. Check `use_cases.py` for examples
2. Run `python verify_setup.py` to diagnose issues
3. Check backend logs for API errors
4. Use browser dev tools to inspect API calls

---

## 🚀 Performance Tips

### Caching
```python
@st.cache_data(ttl=300)
def load_reference_data():
    return api.get_accounts()
```

### Pagination
```python
limit = 50
offset = st.session_state.get('page', 0) * limit
data = api.get_transactions(limit=limit, offset=offset)
```

### Lazy Loading
```python
with st.expander("Advanced Options"):
    # Content loaded only when expanded
    show_advanced_settings()
```

## 📱 Mobile Considerations

- Use `st.columns()` carefully on mobile
- Test with `layout="wide"` in page config
- Keep forms short, use multiple steps if needed
- Tables should scroll horizontally on small screens
