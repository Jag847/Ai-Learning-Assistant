import streamlit as st
import os
from ai_modules import (
    signup_user, login_user,
    run_ai_study_buddy, run_voice_to_notes, show_dashboard
)

st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")
st.markdown("<style>body{background-color:#e8f5e9}</style>", unsafe_allow_html=True)

# ---------------- LOGIN / SIGNUP ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.sidebar.title("🌿 Login / Signup")
    choice = st.sidebar.radio("Choose Action", ["Login", "Signup"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if choice=="Signup" and st.sidebar.button("Sign Up"):
        success, msg = signup_user(username, password)
        st.sidebar.success(msg)
    elif choice=="Login" and st.sidebar.button("Login"):
        if login_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.sidebar.error("Invalid credentials!")
    st.stop()

# ---------------- NAVIGATION ----------------
st.sidebar.title(f"Welcome, {st.session_state.username} 🌱")
page = st.sidebar.radio("Go to", ["AI Study Buddy", "Voice to Notes", "Progress Dashboard", "Settings / Logout"])

# ---------------- PAGES ----------------
if page=="AI Study Buddy":
    run_ai_study_buddy()
elif page=="Voice to Notes":
    run_voice_to_notes()
elif page=="Progress Dashboard":
    show_dashboard()
elif page=="Settings / Logout":
    st.header("⚙️ Settings")
    if st.button("🔄 Reset Progress Data"):
        if os.path.exists("user_progress.json"):
            os.remove("user_progress.json")
        st.success("Progress data reset successfully!")
    if st.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()
