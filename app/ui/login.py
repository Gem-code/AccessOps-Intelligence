import streamlit as st
from configs import ACCESS_KEY

def render_login():
    # If already authenticated, hide login box completely
    if st.session_state.get("authenticated", False):
        return

    with st.expander("🔐 Login Required", expanded=True):
        key = st.text_input("Enter Access Key:", type="password")

        if st.button("Unlock Dashboard"):
            if key == ACCESS_KEY:
                st.session_state["authenticated"] = True

                # Force rerun using new API
                st.rerun()
            else:
                st.error("Invalid key. Try again.")
