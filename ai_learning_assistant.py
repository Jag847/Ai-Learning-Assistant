import streamlit as st
import tempfile, os, json, requests, time
import pandas as pd
import plotly.express as px
from datetime import date
from ai_modules import (
    gemini_api, generate_quiz_from_text, update_quiz_stats, run_ai_quiz, run_voice_quiz
)

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")
PROGRESS_FILE = "user_progress.json"

# -------------------- CSS --------------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {background-color: #2e7d32; color:white; border-radius:8px;}
.stButton>button:hover {background-color:#1b5e20;}
.progress-container {margin-top:10px; background-color:#c8e6c9; border-radius:10px; height:25px; width:100%; overflow:hidden;}
.progress-bar {height:25px; background-color:#43a047; width:0%; transition: width 1s ease-in-out;}
.toast {position:fixed; bottom:30px; right:30px; background: linear-gradient(90deg,#43a047,#66bb6a); color:white; padding:16px 24px; border-radius:12px; font-weight:bold; box-shadow:0 4px 16px rgba(0,0,0,0.3); opacity:0; transform:translateY(30px); animation:toastInOut 4s ease-in-out; z-index:9999;}
@keyframes toastInOut {0%{opacity:0; transform:translateY(30px);}10%{opacity:1; transform:translateY(0);}90%{opacity:1; transform:translateY(0);}100%{opacity:0; transform:translateY(30px);}}
</style>
""", unsafe_allow_html=True)

# -------------------- PROGRESS --------------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "summary": {"correct":0,"wrong":0,"weak":0}, "badges": []}

def save_progress(progress):
    with open(PROGRESS_FILE,"w") as f:
        json.dump(progress,f,indent=4)

progress = load_progress()

# -------------------- NAVIGATION --------------------
st.sidebar.title("🌿 Navigation")
page = st.sidebar.radio("Go to", ["Welcome", "AI Study Buddy", "Voice-to-Notes", "Progress Dashboard", "Settings / Logout"])

# -------------------- WELCOME --------------------
if page == "Welcome":
    st.markdown("<h1 style='color:#2e7d32;'>Let's take a step towards a better Earth 🌍</h1>", unsafe_allow_html=True)
    st.write("Welcome to your AI-powered study companion!")
    if st.button("🚀 Let’s Get Started"):
        st.session_state["page"] = "AI Study Buddy"

# -------------------- AI STUDY BUDDY --------------------
elif page == "AI Study Buddy":
    st.header("🧠 AI Study Buddy")
    st.write("Interactive quizzes, instant feedback, and track your progress.")

    topic = st.text_input("Enter a topic or question for AI answer:")
    if st.button("Get Answer"):
        if topic:
            answer = gemini_api(f"Answer academically and clearly: {topic}")
            st.success(answer)
        else:
            st.warning("Enter a topic/question.")

    st.subheader("🎯 Quiz")
    run_ai_quiz(progress)

# -------------------- VOICE-TO-NOTES --------------------
elif page == "Voice-to-Notes":
    st.header("🎙️ Voice-to-Notes")
    st.write("Speak live or upload lecture audio. Generate notes, summary, or quizzes.")

    tab1, tab2 = st.tabs(["Live Speech", "Upload Audio"])

    with tab1:
        st.subheader("🎤 Live Speech Input")
        run_voice_quiz(progress, live=True)

    with tab2:
        st.subheader("📁 Upload Lecture Audio")
        audio_file = st.file_uploader("Upload audio", type=["mp3","wav","m4a"])
        if audio_file:
            run_voice_quiz(progress, live=False, uploaded_file=audio_file)

# -------------------- PROGRESS DASHBOARD --------------------
elif page == "Progress Dashboard":
    st.header("📊 Study Progress Dashboard")
    if not progress["history"]:
        st.warning("No progress data yet. Take a quiz first!")
    else:
        df = pd.DataFrame(progress["history"])
        st.subheader("📈 Progress Over Time")
        fig_line = px.line(df,x="date",y="score",markers=True,title="Progress Over Time",color_discrete_sequence=["#2e7d32"])
        st.plotly_chart(fig_line,use_container_width=True)

        st.subheader("🥧 Quiz Performance Breakdown")
        summary = progress["summary"]
        fig_pie = px.pie(values=[summary["correct"],summary["wrong"],summary["weak"]],
                         names=["Correct","Wrong","Weak Topics"],
                         color_discrete_sequence=["#66bb6a","#ef5350","#ffee58"],
                         hole=0.4)
        st.plotly_chart(fig_pie,use_container_width=True)

        st.subheader("🏅 Earned Badges")
        if progress.get("badges"):
            st.markdown(", ".join(progress["badges"]))
        else:
            st.info("No badges earned yet.")

# -------------------- SETTINGS --------------------
elif page == "Settings / Logout":
    st.header("⚙️ Settings")
    if st.button("🔄 Reset Progress"):
        if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)
        st.success("Progress reset.")

    if st.button("🔒 Logout"):
        st.success("Logged out.")
