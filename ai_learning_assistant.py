import streamlit as st
import os
from ai_modules import (
    run_ai_study_buddy,
    run_voice_to_notes,
    show_dashboard,
    load_progress,
    save_progress,
    assign_badges,
    display_badges
)

st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

# -------------------- PAGE STYLE --------------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {background-color: #2e7d32; color: white; border-radius: 8px;}
.stButton>button:hover {background-color: #1b5e20;}
.progress-container {margin-top:10px; background-color:#c8e6c9; border-radius:10px; height:25px; width:100%; overflow:hidden;}
.progress-bar {height:25px; background-color:#43a047; width:0%; transition: width 1s ease-in-out;}
.badge {display:inline-block; padding:0.4rem 0.8rem; margin:0.3rem; border-radius:12px; background: linear-gradient(135deg,#ffd700,#ffecb3); color:#4a4a4a; font-weight:700; box-shadow:0 4px 12px rgba(0,0,0,0.25);}
.badge:hover {transform: scale(1.2) rotate(-3deg);}
</style>
""", unsafe_allow_html=True)

# -------------------- LOGIN/SIGNUP --------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.header("🌿 Welcome to AI Learning Assistant")
    choice = st.radio("Select option", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Signup" and st.button("Sign Up"):
        user_file = f"{username}_credentials.json"
        if os.path.exists(user_file):
            st.warning("Username already exists.")
        else:
            with open(user_file, "w") as f:
                json.dump({"username": username, "password": password}, f)
            st.success("Signup successful! Please login.")

    if choice == "Login" and st.button("Login"):
        user_file = f"{username}_credentials.json"
        if os.path.exists(user_file):
            with open(user_file,"r") as f:
                creds = json.load(f)
            if creds["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
            else:
                st.error("Incorrect password.")
        else:
            st.error("User does not exist.")

# -------------------- NAVIGATION --------------------
if st.session_state.get("logged_in", False):
    st.sidebar.title(f"🌿 {st.session_state['username']}'s Dashboard")
    page = st.sidebar.radio("Go to", [
        "AI Study Buddy",
        "Voice to Notes",
        "Progress Dashboard",
        "Settings / Logout"
    ])

    if page == "AI Study Buddy":
        run_ai_study_buddy(st.session_state["username"])
    elif page == "Voice to Notes":
        run_voice_to_notes(st.session_state["username"])
    elif page == "Progress Dashboard":
        show_dashboard(st.session_state["username"])
    elif page == "Settings / Logout":
        st.header("⚙️ Settings")
        if st.button("🔄 Reset Progress Data"):
            progress_file = f"{st.session_state['username']}_progress.json"
            if os.path.exists(progress_file):
                os.remove(progress_file)
            st.success("Progress reset successfully!")
        if st.button("🔒 Logout"):
            st.session_state["logged_in"] = False
            st.success("Logged out successfully.")
