import streamlit as st
import os
import json
from datetime import date
from ai_modules import (
    gemini_api, load_progress, save_progress, assign_badges, display_badges
)
import tempfile

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

# -------------------- CSS --------------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {background-color: #2e7d32; color: white; border-radius: 8px;}
.stButton>button:hover {background-color: #1b5e20;}
.progress-container {margin-top:10px;background-color:#c8e6c9;border-radius:10px;height:25px;width:100%;overflow:hidden;}
.progress-bar {height:25px;background-color:#43a047;width:0%;transition:width 1s ease-in-out;}
.badge {display:inline-block;padding:0.4rem 0.8rem;margin:0.3rem;border-radius:12px;background: linear-gradient(135deg,#ffd700,#ffecb3);color:#4a4a4a;font-weight:700;box-shadow:0 4px 12px rgba(0,0,0,0.25);transition: transform 0.3s ease;}
.badge:hover {transform: scale(1.2) rotate(-3deg);box-shadow:0 6px 20px rgba(0,0,0,0.35);}
</style>
""", unsafe_allow_html=True)

# -------------------- USER AUTH --------------------
USER_FILE = "users.json"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def login_page():
    st.header("🌿 Welcome to AI Learning Assistant")
    tab1, tab2 = st.tabs(["Login", "Signup"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            users = load_users()
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Logged in as {username}")
            else:
                st.error("Invalid credentials!")

    with tab2:
        st.subheader("Signup")
        new_user = st.text_input("Username", key="signup_user")
        new_pass = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Signup"):
            users = load_users()
            if new_user in users:
                st.warning("Username already exists!")
            else:
                users[new_user] = new_pass
                save_users(users)
                st.success("Signup successful! Please login.")

# -------------------- NAVIGATION --------------------
def main_app():
    st.sidebar.title(f"🌿 {st.session_state.username}'s Dashboard")
    page = st.sidebar.radio("Go to", ["Welcome","AI Study Buddy","Voice to Notes","Progress Dashboard","Settings / Logout"])
    
    # -------------------- PAGES --------------------
    if page == "Welcome":
        st.markdown(f"<h1 style='color:#2e7d32;'>Welcome {st.session_state.username}! 🌍</h1>", unsafe_allow_html=True)
        st.write("Let's take a step towards a better Earth with AI-powered learning!")
    
    elif page == "AI Study Buddy":
        from ai_modules import run_ai_study_buddy
        run_ai_study_buddy()
    
    elif page == "Voice to Notes":
        from ai_modules import run_voice_to_notes
        run_voice_to_notes()
    
    elif page == "Progress Dashboard":
        from ai_modules import show_dashboard
        show_dashboard()
    
    elif page == "Settings / Logout":
        st.header("⚙️ Settings")
        if st.button("🔄 Reset Progress Data"):
            if os.path.exists("user_progress.json"):
                os.remove("user_progress.json")
            st.success("Progress data reset successfully!")
        if st.button("🔒 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.success("Logged out successfully!")

# -------------------- EXECUTION --------------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
