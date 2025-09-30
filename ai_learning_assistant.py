import streamlit as st
import tempfile
import os
from datetime import date
from ai_modules import (
    gemini_api, load_progress, save_progress, show_dashboard,
    run_ai_study_buddy, run_voice_to_notes
)

# -------------------- CONFIG --------------------
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
.toast {position:fixed; bottom:30px; right:30px; background: linear-gradient(90deg,#43a047,#66bb6a); color:white; padding:16px 24px; border-radius:12px; font-weight:bold; box-shadow:0 4px 16px rgba(0,0,0,0.3); opacity:0; transform:translateY(30px); animation:toastInOut 4s ease-in-out; z-index:9999;}
@keyframes toastInOut {0%{opacity:0; transform:translateY(30px);} 10%{opacity:1; transform:translateY(0);} 90%{opacity:1; transform:translateY(0);} 100%{opacity:0; transform:translateY(30px);}}
.badge {display:inline-block; padding:0.4rem 0.8rem; margin:0.3rem; border-radius:12px; background: linear-gradient(135deg,#ffd700,#ffecb3); color:#4a4a4a; font-weight:700; box-shadow:0 4px 12px rgba(0,0,0,0.25); transition: transform 0.3s ease;}
.badge:hover {transform: scale(1.2) rotate(-3deg); box-shadow:0 6px 20px rgba(0,0,0,0.35);}
</style>
""", unsafe_allow_html=True)

# -------------------- NAVIGATION --------------------
st.sidebar.title("🌿 Navigation")
page = st.sidebar.radio("Go to", [
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
    if st.button("🚀 Let’s Get Started"):
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
        st.success("You have been logged out successfully.")
