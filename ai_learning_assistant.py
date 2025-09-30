import streamlit as st
import os
from datetime import date
from ai_modules import (
    run_ai_study_buddy,
    run_voice_to_notes,
    show_dashboard,
    load_progress,
    save_progress
)

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

# -------------------- CSS --------------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {background-color: #2e7d32; color: white; border-radius: 8px;}
.stButton>button:hover {background-color: #1b5e20;}
input, .stTextInput>div>input {background-color: #f1f8e9;}
.progress-container {margin-top:10px; background-color:#c8e6c9; border-radius:10px; height:25px; width:100%; overflow:hidden;}
.progress-bar {height:25px; background-color:#43a047; width:0%; transition:width 1s ease-in-out;}
.badge {display:inline-block; padding:0.4rem 0.8rem; margin:0.3rem; border-radius:12px; background: linear-gradient(135deg,#ffd700,#ffecb3); color:#4a4a4a; font-weight:700; box-shadow:0 4px 12px rgba(0,0,0,0.25); transition: transform 0.3s ease;}
.badge:hover {transform: scale(1.2) rotate(-3deg); box-shadow:0 6px 20px rgba(0,0,0,0.35);}
</style>
""", unsafe_allow_html=True)

# -------------------- LOGIN SYSTEM --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.header("🌿 AI Learning Assistant Login")
    st.write("Please enter your credentials to continue.")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # For demo, accept any non-empty username/password
        if username.strip() != "" and password.strip() != "":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome, {username}!")
        else:
            st.error("Invalid username or password.")
    st.stop()  # Stop the app until login is successful

# -------------------- NAVIGATION --------------------
st.sidebar.title(f"🌿 Welcome, {st.session_state.username}")
page = st.sidebar.radio("Navigate to:", [
    "Welcome",
    "AI Study Buddy",
    "Voice to Notes",
    "Progress Dashboard",
    "Settings / Logout"
])

# -------------------- PAGES --------------------
if page == "Welcome":
    st.markdown("<h1 style='color:#2e7d32;'>Let's take a step towards a better Earth 🌍</h1>", unsafe_allow_html=True)
    st.write("Welcome to your AI-powered study companion!")
    st.write("Use this tool to ask questions, generate quizzes, summarize lecture notes, and track your study progress with badges and analytics.")

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
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("You have been logged out successfully!")
        st.experimental_rerun()
