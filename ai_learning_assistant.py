import streamlit as st
import os
import json
from ai_modules import (
    run_ai_study_buddy, run_voice_to_notes, show_dashboard, load_progress, save_progress
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
.flip-card {background-color: #ffffff; border-radius: 10px; padding: 20px; margin: 10px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.2); cursor: pointer;}
.flip-card-front {background-color: #f0f4f8; color: #333; padding: 15px; border-radius: 10px;}
.flip-card-back {background-color: #e3f2fd; color: #333; padding: 15px; border-radius: 10px;}
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
            with open(user_file, "r") as f:
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

    # Side history bar
    progress = load_progress(st.session_state["username"])
    chat_history = progress.get("chat_history", [])
    with st.sidebar.expander("📜 History", expanded=False):
        if chat_history:
            for idx, entry in enumerate(chat_history):
                label = f"{entry['type']}: {entry['content'][:30]}..."
                if st.button(label, key=f"hist_{idx}"):
                    st.session_state["selected_history"] = entry
        else:
            st.info("No history yet.")

    if page == "AI Study Buddy":
        run_ai_study_buddy(st.session_state["username"])
        # Display selected history if any
        if "selected_history" in st.session_state:
            st.subheader("Selected History Entry")
            entry = st.session_state["selected_history"]
            if entry["type"] == "Question":
                st.markdown(f"**Question:** {entry['content']}")
                st.markdown(f"**Answer:** {entry['answer']}")
            elif entry["type"] == "Flashcards":
                st.markdown(f"**Flashcards Generated for Topic:** {entry['content']}")
                st.markdown(f"**Number of Cards:** {entry['num_cards']}")
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
