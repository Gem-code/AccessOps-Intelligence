import streamlit as st

def render_login():
    with st.expander("🔐 Login Required"):
        key = st.text_input("Enter Access Key:", type="password")

        if st.button("Unlock Dashboard"):
            if key == "demo-key":
                st.session_state["authenticated"] = True
                st.success("Access granted!")
            else:
                st.error("Invalid key. Try again.")
