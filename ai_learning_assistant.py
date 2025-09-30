import streamlit as st
import tempfile
import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
PROGRESS_FILE = "user_progress.json"

# -------------------- PAGE STYLE --------------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {
    background-color: #2e7d32;
    color: white;
    border-radius: 8px;
}
.stButton>button:hover {background-color: #1b5e20;}
.progress-container {
    margin-top: 10px;
    background-color: #c8e6c9;
    border-radius: 10px;
    height: 25px;
    width: 100%;
    overflow: hidden;
}
.progress-bar {
    height: 25px;
    background-color: #43a047;
    width: 0%;
    transition: width 1s ease-in-out;
}
.toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: linear-gradient(90deg, #43a047, #66bb6a);
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    font-weight: bold;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    opacity: 0;
    transform: translateY(30px);
    animation: toastInOut 4s ease-in-out;
    z-index: 9999;
}
@keyframes toastInOut {
    0% {opacity: 0; transform: translateY(30px);}
    10% {opacity: 1; transform: translateY(0);}
    90% {opacity: 1; transform: translateY(0);}
    100% {opacity: 0; transform: translateY(30px);}
}
</style>
""", unsafe_allow_html=True)

# -------------------- GEMINI CALL --------------------
def gemini_api(prompt: str):
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ API Error: {e}"

# -------------------- PROGRESS STORAGE --------------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "summary": {"correct": 0, "wrong": 0, "weak": 0}}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

progress = load_progress()

# -------------------- NAVIGATION --------------------
st.sidebar.title("🌿 Navigation")
page = st.sidebar.radio("Go to", [
    "Welcome",
    "AI Study Buddy",
    "Web Dev & Weak Topics",
    "Progress Dashboard",
    "Settings / Logout"
])

# -------------------- WELCOME --------------------
if page == "Welcome":
    st.markdown("<h1 style='color:#2e7d32;'>Let's take a step towards a better Earth 🌍</h1>", unsafe_allow_html=True)
    st.write("Welcome to your AI-powered study companion!")
    if st.button("🚀 Let’s Get Started"):
        st.session_state["page"] = "AI Study Buddy"

# -------------------- STUDY BUDDY --------------------
elif page == "AI Study Buddy":
    st.header("🧠 AI Study Buddy")
    st.write("Take quizzes, get instant feedback, and track your progress.")

    question = st.text_input("Enter your question or topic:")
    if st.button("Get Answer"):
        if question:
            answer = gemini_api(f"Answer this academic question clearly: {question}")
            st.success(answer)
        else:
            st.warning("Please enter a question.")

    st.subheader("🎯 Quiz Time")
    topic = st.text_input("Enter a quiz topic:")
    if st.button("Generate Quiz"):
        quiz = gemini_api(f"Create 5 quiz questions with 4 options each on {topic}. Mark the correct answer clearly.")
        st.markdown(quiz)

    st.subheader("📈 Record Your Quiz Performance")
    col1, col2, col3 = st.columns(3)
    with col1:
        correct = st.number_input("Correct Answers", min_value=0, value=0)
    with col2:
        wrong = st.number_input("Wrong Answers", min_value=0, value=0)
    with col3:
        weak = st.number_input("Weak Topics Identified", min_value=0, value=0)

    if st.button("💾 Save Progress"):
        new_score = max(0, min(100, (correct * 10) + 50 - weak * 5))
        progress["history"].append({
            "date": str(date.today()),
            "score": new_score
        })
        progress["summary"]["correct"] += correct
        progress["summary"]["wrong"] += wrong
        progress["summary"]["weak"] += weak
        save_progress(progress)

        # Animated development bar
        st.markdown("<h4 style='color:#2e7d32;'>📊 Development Progress</h4>", unsafe_allow_html=True)
        bar_html = f"""
        <div class="progress-container">
            <div class="progress-bar" style="width:{new_score}%;"></div>
        </div>
        <p style='color:#1b5e20;'>Your latest quiz score: {new_score}%</p>
        """
        st.markdown(bar_html, unsafe_allow_html=True)

        # ✅ Toast notification
        toast_html = """
        <div class="toast">🎉 Progress updated successfully!</div>
        <script>
        setTimeout(() => {{
            const toast = document.querySelector('.toast');
            if (toast) toast.remove();
        }}, 4000);
        </script>
        """
        st.markdown(toast_html, unsafe_allow_html=True)

# -------------------- WEB DEV + WEAK TOPICS --------------------
elif page == "Web Dev & Weak Topics":
    st.header("💻 Web Development + Weak Topics")
    st.write("Study weak areas and generate notes with voice input.")

    tab1, tab2 = st.tabs(["Weak Topics", "Voice to Notes"])

    with tab1:
        st.subheader("🧩 Identify Weak Topics")
        subject = st.text_input("Enter your subject or web topic:")
        if st.button("Analyze Weak Areas"):
            analysis = gemini_api(f"List weak areas in {subject} and how to improve them.")
            st.markdown(analysis)

    with tab2:
        st.subheader("🎙️ Voice to Notes Generator")
        audio_file = st.file_uploader("Upload a lecture audio file", type=["mp3", "wav", "m4a"])
        if audio_file:
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(audio_file.read())
                temp_path = temp.name
            st.info("Transcribing... please wait.")
            transcription = gemini_api("Convert this uploaded lecture audio to summarized study notes.")
            st.success(transcription)
            os.remove(temp_path)

# -------------------- PROGRESS DASHBOARD --------------------
elif page == "Progress Dashboard":
    st.header("📊 Study Progress Dashboard")

    if not progress["history"]:
        st.warning("No progress data available yet. Take a quiz first!")
    else:
        df = pd.DataFrame(progress["history"])

        st.subheader("📈 Progress Over Time")
        plt.figure()
        plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
        plt.xlabel("Date")
        plt.ylabel("Quiz Score (%)")
        plt.title("Your Study Progress Over Time")
        st.pyplot(plt)

        st.subheader("🥧 Quiz Performance Breakdown")
        summary = progress["summary"]
        labels = ["Correct", "Wrong", "Weak Topics"]
        values = [summary["correct"], summary["wrong"], summary["weak"]]
        plt.figure()
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140,
                colors=["#66bb6a", "#ef5350", "#ffee58"])
        plt.title("Overall Quiz Data Analytics")
        st.pyplot(plt)

# -------------------- SETTINGS --------------------
elif page == "Settings / Logout":
    st.header("⚙️ Settings")
    st.write("Manage your preferences or log out.")

    if st.button("🔄 Reset Progress Data"):
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        st.success("Progress data reset successfully!")

    if st.button("🔒 Logout"):
        st.success("You have been logged out successfully.")
