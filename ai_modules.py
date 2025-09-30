import streamlit as st
import requests
import json
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
PROGRESS_FILE = "user_progress.json"

# -------------------- GEMINI API --------------------
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
        with open(PROGRESS_FILE,"r") as f:
            return json.load(f)
    return {"history": [], "summary":{"correct":0,"wrong":0,"weak":0}, "badges":[]}

def save_progress(progress):
    with open(PROGRESS_FILE,"w") as f:
        json.dump(progress,f,indent=4)

# -------------------- BADGES --------------------
def assign_badges(progress, score):
    badges = progress.get("badges",[])
    if score >= 80 and "🌟 High Scorer" not in badges:
        badges.append("🌟 High Scorer")
    if len(progress.get("history",[])) >= 5 and "🔥 Consistent Learner" not in badges:
        badges.append("🔥 Consistent Learner")
    if len(progress.get("history",[])) == 1 and "🎯 First Quiz Completed" not in badges:
        badges.append("🎯 First Quiz Completed")
    progress["badges"] = badges

def display_badges(progress):
    badges = progress.get("badges",[])
    if badges:
        badge_html = ""
        for b in badges:
            badge_html += f"<div class='badge'>{b}</div>"
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.info("No badges earned yet.")

# -------------------- AI STUDY BUDDY --------------------
def run_ai_study_buddy():
    st.header("🧠 AI Study Buddy")
    question = st.text_input("Ask a question or topic:")
    if st.button("Get Answer"):
        if question:
            answer = gemini_api(f"Answer this academic question clearly: {question}")
            st.success(answer)
        else:
            st.warning("Enter a question!")

    st.subheader("🎯 Quiz Time")
    topic = st.text_input("Enter quiz topic:")
    if st.button("Generate Quiz"):
        quiz_text = gemini_api(f"Generate 5 quiz questions with 4 options each on {topic}. Mark the correct answer clearly.")
        st.markdown(quiz_text)

    st.subheader("📈 Record Quiz Performance")
    progress = load_progress()
    col1,col2,col3 = st.columns(3)
    with col1: correct = st.number_input("Correct", min_value=0, value=0)
    with col2: wrong = st.number_input("Wrong", min_value=0, value=0)
    with col3: weak = st.number_input("Weak Topics", min_value=0, value=0)

    if st.button("💾 Save Progress"):
        new_score = max(0,min(100,(correct*10)+50-weak*5))
        progress["history"].append({"date": str(date.today()),"score": new_score})
        progress["summary"]["correct"] += correct
        progress["summary"]["wrong"] += wrong
        progress["summary"]["weak"] += weak
        assign_badges(progress,new_score)
        save_progress(progress)
        st.success(f"Progress saved! Latest Score: {new_score}")
        display_badges(progress)

# -------------------- VOICE TO NOTES --------------------
def run_voice_to_notes():
    st.header("🎙️ Voice to Notes")
    audio_file = st.file_uploader("Upload lecture audio", type=["mp3","wav","m4a"])
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(audio_file.read())
            temp_path = temp.name
        st.info("Transcribing... please wait")
        transcription = gemini_api("Convert this audio into summarized study notes.")
        st.success(transcription)
        if st.button("Generate Quiz from Notes"):
            quiz_text = gemini_api(f"Generate 5 quiz questions based on this transcript:\n{transcription}")
            st.markdown(quiz_text)
        if st.button("Summarize Notes"):
            summary = gemini_api(f"Summarize these notes:\n{transcription}")
            st.markdown(summary)
        os.remove(temp_path)

# -------------------- DASHBOARD --------------------
def show_dashboard():
    st.header("📊 Study Progress Dashboard")
    progress = load_progress()
    history = progress.get("history", [])
    if not history:
        st.warning("No quiz data yet. Take a quiz first!")
        return
    df = pd.DataFrame(history)

    # Latest score progress bar
    latest_score = df.iloc[-1]["score"]
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width:{latest_score}%;"></div>
    </div>
    <p style='color:#1b5e20;'>Latest Quiz Score: {latest_score}%</p>
    """, unsafe_allow_html=True)

    # Line plot
    st.subheader("📈 Progress Over Time")
    plt.figure()
    plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
    plt.xlabel("Date")
    plt.ylabel("Score (%)")
    plt.title("Quiz Score Progress")
    st.pyplot(plt)

    # Pie chart
    st.subheader("🥧 Quiz Performance Analytics")
    summary = progress.get("summary",{})
    labels = ["Correct","Wrong","Weak Topics"]
    values = [summary.get("correct",0), summary.get("wrong",0), summary.get("weak",0)]
    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#66bb6a","#ef5350","#ffee58"])
    plt.title("Overall Quiz Analytics")
    st.pyplot(plt)

    # Floating badges
    st.subheader("🏅 Badges Earned")
    display_badges(progress)
