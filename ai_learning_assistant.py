import streamlit as st
import os
import json
from ai_modules import run_ai_study_buddy, show_dashboard, load_progress

st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

# -------------------- PAGE STYLE --------------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {background-color: #2e7d32; color: white; border-radius: 8px;}
.stButton>button:hover {background-color: #1b5e20;}
.badge {display:inline-block; padding:0.4rem 0.8rem; margin:0.3rem; border-radius:12px;
background: linear-gradient(135deg,#ffd700,#ffecb3); color:#4a4a4a; font-weight:700;
box-shadow:0 4px 12px rgba(0,0,0,0.25);}
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
            st.error("User not found.")

# -------------------- APP NAVIGATION --------------------
if st.session_state.get("logged_in", False):
    st.sidebar.title(f"🌿 {st.session_state['username']}'s Dashboard")
    page = st.sidebar.radio("Go to", [
        "AI Study Buddy",
        "Progress Dashboard",
        "Settings / Logout"
    ])

    # -------------------- HISTORY BAR --------------------
    progress = load_progress(st.session_state["username"])
    history = progress.get("chat_history", [])
    with st.sidebar.expander("📜 History", expanded=False):
        if history:
            for idx, entry in enumerate(reversed(history)):
                label = f"{entry['type']}: {entry['content'][:30]}"
                if st.button(label, key=f"hist_{idx}"):
                    st.session_state["selected_history"] = entry
        else:
            st.info("No history yet.")

    # -------------------- PAGE HANDLERS --------------------
    if page == "AI Study Buddy":
        run_ai_study_buddy(st.session_state["username"])

        # Display selected history if any
        if "selected_history" in st.session_state:
            st.subheader("🧾 History Entry Details")
            entry = st.session_state["selected_history"]
            if entry["type"] == "Question":
                st.markdown(f"**Question:** {entry['content']}")
                st.markdown(f"**Answer:** {entry.get('answer', 'N/A')}")
            elif entry["type"] == "Flashcards":
                st.markdown(f"**Flashcards Topic:** {entry['content']}")
                st.markdown(f"**Number of Cards:** {entry['num_cards']}")
            elif entry["type"] == "Quiz":
                st.markdown(f"**Quiz Topic:** {entry['content']}")
                st.markdown(f"**Questions:** {entry['num_questions']}")
                for quiz in progress.get("quizzes", []):
                    if quiz["topic"] == entry["content"]:
                        st.text_area("Quiz Content", value=quiz["content"], height=400)

    elif page == "Progress Dashboard":
        show_dashboard(st.session_state["username"])

    elif page == "Settings / Logout":
        st.header("⚙️ Settings")
        progress_file = f"{st.session_state['username']}_progress.json"
        if st.button("🔄 Reset Progress Data"):
            if os.path.exists(progress_file):
                os.remove(progress_file)
                st.success("Progress reset successfully!")
        if st.button("🔒 Logout"):
            st.session_state["logged_in"] = False
            st.success("Logged out successfully.")
