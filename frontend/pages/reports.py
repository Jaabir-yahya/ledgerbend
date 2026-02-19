"""Reports page - Financial reports and analysis."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from api_client import api

st.markdown('<p class="main-header">📈 Reports</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Financial reports and analysis</p>', unsafe_allow_html=True)

# Date range selector for reports that need it
col1, col2 = st.columns(2)
with col1:
    report_start = st.date_input("Period Start", value=date.today() - timedelta(days=30))
with col2:
    report_end = st.date_input("Period End", value=date.today())

tab_trial, tab_pl, tab_bs, tab_cf, tab_exposure = st.tabs([
    "📊 Trial Balance", "💰 Income Statement", "📋 Balance Sheet", 
    "💸 Cash Flow", "💱 Currency Exposure"
])

with tab_trial:
    st.subheader("Trial Balance")
    st.markdown("*Debits must equal credits - the fundamental accounting equation*")
    
    try:
        trial_balance = api.get_trial_balance()
        
        if trial_balance:
            df = pd.DataFrame(trial_balance)
            
            # Format amounts
            df['debit_balance'] = df['debit_balance'].apply(lambda x: f"KES {x:,.2f}" if x > 0 else "")
            df['credit_balance'] = df['credit_balance'].apply(lambda x: f"KES {x:,.2f}" if x > 0 else "")
            
            display_df = df[['account_code', 'account_name', 'account_type', 'debit_balance', 'credit_balance']].copy()
            display_df.columns = ['Code', 'Account', 'Type', 'Debits', 'Credits']
            
            # Color by account type
            def color_type(val):
                colors = {
                    'asset': 'background-color: #d4edda',
                    'liability': 'background-color: #f8d7da',
                    'equity': 'background-color: #d1ecf1',
                    'income': 'background-color: #fff3cd',
                    'expense': 'background-color: #f0f0f0'
                }
                return colors.get(val.lower(), '')
            
            st.dataframe(
                display_df.style.applymap(color_type, subset=['Type']),
                use_container_width=True,
                hide_index=True
            )
            
            # Totals
            total_debits = sum(row['debit_balance'] for row in trial_balance if row.get('debit_balance', 0) > 0)
            total_credits = sum(row['credit_balance'] for row in trial_balance if row.get('credit_balance', 0) > 0)
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Debits", f"KES {total_debits:,.2f}")
            with col2:
                st.metric("Total Credits", f"KES {total_credits:,.2f}")
            with col3:
                if abs(total_debits - total_credits) < 0.01:
                    st.success("✅ Balanced")
                else:
                    st.error(f"❌ Diff: {abs(total_debits - total_credits):,.2f}")
        else:
            st.info("No trial balance data available")
    except Exception as e:
        st.error(f"Error loading trial balance: {e}")

with tab_pl:
    st.subheader("Income Statement (P&L)")
    st.markdown(f"*Period: {report_start} to {report_end}*")
    
    try:
        # Get summary
        pl_summary = api.get_income_statement_summary(
            start_date=report_start.strftime('%Y-%m-%d'),
            end_date=report_end.strftime('%Y-%m-%d')
        )
        
        # Get detailed
        pl_detail = api.get_income_statement(
            start_date=report_start.strftime('%Y-%m-%d'),
            end_date=report_end.strftime('%Y-%m-%d')
        )
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Income", f"KES {pl_summary.get('total_income', 0):,.2f}")
        with col2:
            st.metric("Total Expenses", f"KES {pl_summary.get('total_expenses', 0):,.2f}")
        with col3:
            net = pl_summary.get('net_profit', 0)
            st.metric("Net Profit", f"KES {net:,.2f}", 
                     delta=f"{pl_summary.get('profit_margin', 0):.1f}% margin",
                     delta_color="normal" if net >= 0 else "inverse")
        with col4:
            st.metric("COGS", f"KES {pl_summary.get('total_cogs', 0):,.2f}")
        
        # Detailed breakdown
        st.divider()
        st.subheader("Detailed Breakdown")
        
        if pl_detail.get('income'):
            with st.expander("Revenue Accounts", expanded=True):
                income_df = pd.DataFrame(pl_detail['income'])
                income_df['amount'] = income_df['amount'].apply(lambda x: f"KES {x:,.2f}")
                st.dataframe(income_df[['account_code', 'account_name', 'amount']], 
                           use_container_width=True, hide_index=True)
        
        if pl_detail.get('expenses'):
            with st.expander("Expense Accounts"):
                expense_df = pd.DataFrame(pl_detail['expenses'])
                expense_df['amount'] = expense_df['amount'].apply(lambda x: f"KES {x:,.2f}")
                st.dataframe(expense_df[['account_code', 'account_name', 'amount']], 
                           use_container_width=True, hide_index=True)
        
        # Visualization
        if pl_detail.get('income') or pl_detail.get('expenses'):
            st.divider()
            st.subheader("Visual Analysis")
            
            chart_data = []
            for item in pl_detail.get('income', []):
                chart_data.append({'Category': item['account_name'], 'Amount': item['amount'], 'Type': 'Income'})
            for item in pl_detail.get('expenses', []):
                chart_data.append({'Category': item['account_name'], 'Amount': -item['amount'], 'Type': 'Expense'})
            
            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                fig = px.bar(chart_df, x='Category', y='Amount', color='Type',
                           title='Income vs Expenses by Account',
                           color_discrete_map={'Income': '#28a745', 'Expense': '#dc3545'})
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error loading income statement: {e}")

with tab_bs:
    st.subheader("Balance Sheet")
    st.markdown(f"*As of: {report_end}*")
    
    try:
        # Summary
        bs_summary = api.get_balance_sheet_summary(date_to=report_end.strftime('%Y-%m-%d'))
        
        # Detailed
        bs_detail = api.get_balance_sheet(date_to=report_end.strftime('%Y-%m-%d'))
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Assets", f"KES {bs_summary.get('total_assets', 0):,.2f}")
        with col2:
            st.metric("Total Liabilities", f"KES {bs_summary.get('total_liabilities', 0):,.2f}")
        with col3:
            st.metric("Total Equity", f"KES {bs_summary.get('total_equity', 0):,.2f}")
        with col4:
            is_balanced = bs_summary.get('is_balanced', False)
            if is_balanced:
                st.success("✅ Balanced")
            else:
                st.error("❌ Not Balanced")
        
        # Verification
        st.divider()
        assets = bs_summary.get('total_assets', 0)
        liab_eq = bs_summary.get('total_liabilities', 0) + bs_summary.get('total_equity', 0)
        
        if abs(assets - liab_eq) < 0.01:
            st.success(f"✅ Assets = Liabilities + Equity (KES {assets:,.2f})")
        else:
            st.error(f"❌ Discrepancy: KES {abs(assets - liab_eq):,.2f}")
        
        # Detailed breakdown
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if bs_detail.get('assets'):
                with st.expander("Assets", expanded=True):
                    assets_df = pd.DataFrame(bs_detail['assets'])
                    assets_df['balance'] = assets_df['balance'].apply(lambda x: f"KES {x:,.2f}")
                    st.dataframe(assets_df[['account_code', 'account_name', 'balance']], 
                               use_container_width=True, hide_index=True)
            
            if bs_detail.get('liabilities'):
                with st.expander("Liabilities"):
                    liab_df = pd.DataFrame(bs_detail['liabilities'])
                    liab_df['balance'] = liab_df['balance'].apply(lambda x: f"KES {x:,.2f}")
                    st.dataframe(liab_df[['account_code', 'account_name', 'balance']], 
                               use_container_width=True, hide_index=True)
        
        with col2:
            if bs_detail.get('equity'):
                with st.expander("Equity"):
                    equity_df = pd.DataFrame(bs_detail['equity'])
                    equity_df['balance'] = equity_df['balance'].apply(lambda x: f"KES {x:,.2f}")
                    st.dataframe(equity_df[['account_code', 'account_name', 'balance']], 
                               use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error loading balance sheet: {e}")

with tab_cf:
    st.subheader("Cash Flow Statement")
    st.markdown(f"*Period: {report_start} to {report_end}*")
    
    try:
        cf = api.get_cash_flow(
            start_date=report_start.strftime('%Y-%m-%d'),
            end_date=report_end.strftime('%Y-%m-%d')
        )
        
        if cf.get('entries'):
            df = pd.DataFrame(cf['entries'])
            
            # Format
            df['debit_amount'] = df['debit_amount'].apply(lambda x: f"KES {x:,.2f}" if x > 0 else "")
            df['credit_amount'] = df['credit_amount'].apply(lambda x: f"KES {x:,.2f}" if x > 0 else "")
            
            display_df = df[['date', 'transaction_number', 'account_name', 'debit_amount', 'credit_amount', 'description']].copy()
            display_df.columns = ['Date', 'Transaction', 'Account', 'Inflow', 'Outflow', 'Description']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Summary
            st.divider()
            summary = cf.get('summary', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Inflows", f"KES {summary.get('total_inflows', 0):,.2f}")
            with col2:
                st.metric("Total Outflows", f"KES {summary.get('total_outflows', 0):,.2f}")
            with col3:
                net = summary.get('net_change', 0)
                st.metric("Net Change", f"KES {net:,.2f}", 
                         delta_color="normal" if net >= 0 else "inverse")
        else:
            st.info("No cash flow data for the selected period")
    except Exception as e:
        st.error(f"Error loading cash flow: {e}")

with tab_exposure:
    st.subheader("Currency Exposure Report")
    st.markdown("*Net positions by foreign currency*")
    
    try:
        exposure = api.get_currency_exposure()
        
        if exposure:
            df = pd.DataFrame(exposure)
            
            # Filter out base currency for FX focus
            fx_df = df[df['currency_code'] != 'KES'].copy()
            
            if not fx_df.empty:
                # Format
                fx_df['net_amount'] = fx_df['net_amount'].apply(lambda x: f"{x:,.2f}")
                fx_df['net_base_amount'] = fx_df['net_base_amount'].apply(lambda x: f"KES {x:,.2f}")
                fx_df['avg_rate'] = fx_df['avg_rate'].apply(lambda x: f"{x:.4f}")
                
                display_df = fx_df[['currency_code', 'net_amount', 'net_base_amount', 'avg_rate', 'entry_count']].copy()
                display_df.columns = ['Currency', 'Net Amount', 'Base Value (KES)', 'Avg Rate', 'Entries']
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Visualization
                st.divider()
                chart_data = []
                for _, row in fx_df.iterrows():
                    chart_data.append({
                        'Currency': row['currency_code'],
                        'Net Position (KES)': float(row['net_base_amount'].replace('KES ', '').replace(',', ''))
                    })
                
                chart_df = pd.DataFrame(chart_data)
                fig = px.bar(chart_df, x='Currency', y='Net Position (KES)',
                           title='Net Currency Positions',
                           color='Net Position (KES)',
                           color_continuous_scale=['red', 'yellow', 'green'])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No foreign currency exposure")
        else:
            st.info("No currency exposure data available")
    except Exception as e:
        st.error(f"Error loading currency exposure: {e}")
