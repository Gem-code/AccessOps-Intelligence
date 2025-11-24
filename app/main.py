import streamlit as st
from ui.login import render_login
from ui.form_page import render_form_page
from ui.history_page import render_history_page
from ui.insights_page import render_insights_page

from core.configs import APP_TITLE, APP_SUBTITLE

from core.state_manager import init_history

# Page Config
st.set_page_config(page_title=APP_TITLE, page_icon="🛡️", layout="wide")

# Initialize session state keys (history, prefill)
init_history()
if "prefill" not in st.session_state:
    st.session_state["prefill"] = {}

# Load CSS
with open("app/assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Title
st.markdown(f"<div class='title'>{APP_TITLE}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>{APP_SUBTITLE}</div>", unsafe_allow_html=True)

# Authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

render_login()

# If not authenticated, stop here
if not st.session_state["authenticated"]:
    st.stop()

# Main Tabs
form_tab, history_tab, insights_tab = st.tabs(["📝 Request Form", "📜 History", "📈 Insights"])

with form_tab:
    render_form_page()

with history_tab:
    render_history_page()

with insights_tab:
    render_insights_page()
