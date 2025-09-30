import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date
from ai_modules import gemini_api, run_ai_quiz, run_voice_quiz, load_progress, save_progress

PROGRESS_FILE = "user_progress.json"
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

# -------------------- CSS --------------------
def inject_css():
    st.markdown("""
    <style>
    body {background-color: #e8f5e9;}
    .sidebar .sidebar-content {background-color: #c8e6c9;}
    .stButton>button {background-color: #2e7d32;color:white;border-radius:8px;}
    .stButton>button:hover {background-color:#1b5e20;}
    </style>
    """, unsafe_allow_html=True)

inject_css()

progress = load_progress(PROGRESS_FILE)

# -------------------- NAVIGATION --------------------
st.sidebar.title("🌿 Navigation")
page = st.sidebar.radio("Go to", ["Welcome", "AI Study Buddy", "Voice to Notes", "Progress Dashboard", "Settings / Logout"])

# -------------------- PAGES --------------------
if page == "Welcome":
    st.markdown("<h1 style='color:#2e7d32;'>Let's take a step towards a better Earth 🌍</h1>", unsafe_allow_html=True)
    if st.button("🚀 Let's Get Started"):
        st.experimental_rerun()

elif page == "AI Study Buddy":
    st.header("🧠 AI Study Buddy")
    run_ai_quiz()

elif page == "Voice to Notes":
    st.header("🎙️ Voice to Notes")
    run_voice_quiz()

elif page == "Progress Dashboard":
    st.header("📊 Study Progress")
    if not progress["history"]:
        st.warning("No progress data available.")
    else:
        df = pd.DataFrame(progress["history"])
        st.subheader("📈 Progress Over Time")
        plt.figure()
        plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
        plt.xlabel("Date")
        plt.ylabel("Score (%)")
        st.pyplot(plt)

        st.subheader("🥧 Quiz Performance")
        summary = progress["summary"]
        labels = ["Correct", "Wrong"]
        values = [summary["correct"], summary["wrong"]]
        plt.figure()
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#66bb6a", "#ef5350"])
        st.pyplot(plt)

elif page == "Settings / Logout":
    st.header("⚙️ Settings")
    if st.button("Reset Progress Data"):
        if PROGRESS_FILE:
            os.remove(PROGRESS_FILE)
        st.success("Progress reset successfully!")
