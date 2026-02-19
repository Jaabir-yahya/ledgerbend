"""Utility components for consistent UI elements."""
import streamlit as st
import time
from typing import Optional, Callable, Any
import traceback

def loading_spinner(text: str = "Loading..."):
    """Context manager for showing loading spinner."""
    return st.spinner(text)

def show_error(message: str, details: Optional[str] = None):
    """Display error message with optional details."""
    st.markdown('<div class="error-box">', unsafe_allow_html=True)
    st.error(f"❌ {message}")
    if details:
        with st.expander("Error Details"):
            st.code(details)
    st.markdown('</div>', unsafe_allow_html=True)

def show_success(message: str, auto_hide: bool = False):
    """Display success message."""
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.success(f"✅ {message}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if auto_hide:
        time.sleep(3)
        st.empty()

def show_warning(message: str):
    """Display warning message."""
    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
    st.warning(f"⚠️ {message}")
    st.markdown('</div>', unsafe_allow_html=True)

def show_info(message: str):
    """Display info message."""
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.info(f"ℹ️ {message}")
    st.markdown('</div>', unsafe_allow_html=True)

def api_call_with_loading(
    func: Callable,
    *args,
    loading_text: str = "Loading...",
    error_prefix: str = "Operation failed",
    **kwargs
) -> Optional[Any]:
    """Execute API call with loading spinner and error handling."""
    with loading_spinner(loading_text):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error_detail = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            show_error(error_prefix, error_detail)
            return None

def empty_state(icon: str = "📭", message: str = "No data available"):
    """Display empty state message."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; color: #666;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
            <div style="font-size: 1.2rem;">{message}</div>
        </div>
        """, unsafe_allow_html=True)

def metric_card(label: str, value: str, delta: Optional[str] = None, help_text: Optional[str] = None):
    """Display a styled metric card."""
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    if help_text:
        st.metric(label=label, value=value, delta=delta, help=help_text)
    else:
        st.metric(label=label, value=value, delta=delta)
    st.markdown('</div>', unsafe_allow_html=True)

def section_header(title: str, description: Optional[str] = None):
    """Display a section header."""
    st.markdown(f'<p class="main-header">{title}</p>', unsafe_allow_html=True)
    if description:
        st.markdown(f'<p class="sub-header">{description}</p>', unsafe_allow_html=True)

def confirm_dialog(title: str, message: str) -> bool:
    """Show a confirmation dialog."""
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"✅ Yes, {title}", use_container_width=True):
            return True
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            return False
    st.warning(message)
    return None
