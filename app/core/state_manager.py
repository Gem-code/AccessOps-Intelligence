import json
import os
from core.configs import HISTORY_FILE

def init_history():
    if "history" not in getattr(__import__('streamlit').session_state, "history", {}):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    __import__('streamlit').session_state["history"] = json.load(f)
            except:
                __import__('streamlit').session_state["history"] = []
        else:
            __import__('streamlit').session_state["history"] = []

def save_history_entry(entry):
    import streamlit as st
    st.session_state["history"].insert(0, entry)
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(st.session_state["history"], f, indent=2)
    except Exception as e:
        st.warning(f"Could not save history.json: {e}")
