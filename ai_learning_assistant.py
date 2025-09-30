import streamlit as st
import os
import json
from ai_modules import (
    run_ai_study_buddy, run_voice_to_notes, show_dashboard,
    load_progress, save_progress
)

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

USERS_FILE = "users.json"

# -------------------- CSS --------------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {background-color: #2e7d32; color:white; border-radius:8px;}
.stButton>button:hover {background-color:#1b5e20;}
</style>
""", unsafe_allow_html=True)

# -------------------- USER MANAGEMENT --------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def signup():
    st.subheader("📝 Sign Up")
    username = st.text_input("Username", key="signup_user")
    password = st.text_input("Password", type="password", key="signup_pass")
    if st.button("Sign Up"):
        users = load_users()
        if username in users:
            st.error("Username already exists!")
        else:
            users[username] = {"password": password, "progress": {}}
            save_users(users)
            st.success("Signup successful! Please log in.")

def login():
    st.subheader("🔑 Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        users = load_users()
        if username in users and users[username]["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
        else:
            st.error("Invalid credentials!")

# -------------------- NAVIGATION --------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    tab = st.tabs(["Login", "Sign Up"])
    with tab[0]:
        login()
    with tab[1]:
        signup()
else:
    st.sidebar.title(f"🌿 Welcome {st.session_state['username']}")
    page = st.sidebar.radio("Go to", [
        "Welcome",
        "AI Study Buddy",
        "Voice to Notes",
        "Progress Dashboard",
        "Settings / Logout"
    ])

    if page == "Welcome":
        st.markdown("<h1 style='color:#2e7d32;'>Let's take a step towards a better Earth 🌍</h1>", unsafe_allow_html=True)
        st.write("Welcome to your AI-powered study companion!")
        if st.button("🚀 Start Learning"):
            st.session_state["page"] = "AI Study Buddy"

    elif page == "AI Study Buddy":
        run_ai_study_buddy()

    elif page == "Voice to Notes":
        run_voice_to_notes()

    elif page == "Progress Dashboard":
        show_dashboard()

    elif page == "Settings / Logout":
        st.header("⚙️ Settings")
        if st.button("🔄 Reset Progress Data"):
            if os.path.exists("user_progress.json"):
                os.remove("user_progress.json")
            st.success("Progress data reset successfully!")
        if st.button("🔒 Logout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.success("Logged out successfully.")
