import streamlit as st
import requests
import json
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

API_KEY = "YOUR_API_KEY_HERE"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

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
def load_progress(filename):
    if os.path.exists(filename):
        with open(filename,"r") as f:
            return json.load(f)
    return {"history": [], "summary":{"correct":0,"wrong":0,"weak":0}, "badges":[]}

def save_progress(filename, progress):
    with open(filename,"w") as f:
        json.dump(progress,f,indent=4)

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
def run_ai_study_buddy(username):
    st.header("🧠 AI Study Buddy")
    topic = st.text_input("Enter topic/question for AI to answer:")
    if st.button("Get Answer"):
        if topic:
            answer = gemini_api(f"Explain this clearly: {topic}")
            st.success(answer)
        else:
            st.warning("Enter a topic/question.")

    st.subheader("🎯 Generate Quiz")
    quiz_topic = st.text_input("Enter quiz topic for interactive quiz:")
    progress_file = f"{username}_progress.json"
    
    if st.button("Generate Quiz"):
        quiz_text = gemini_api(f"Generate 5 multiple-choice questions (A-D) on {quiz_topic} in JSON without answers")
        try:
            st.session_state.ai_quiz = json.loads(quiz_text)
            st.session_state.ai_answers = {}
        except:
            st.error("Failed to generate quiz. Try another topic.")

    # Display quiz questions and input fields
    quiz = st.session_state.get("ai_quiz", [])
    if quiz:
        st.subheader("📝 Answer the Quiz")
        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            for idx, opt in enumerate(q['options']):
                st.markdown(f"{chr(65+idx)}. {opt}")
            ans = st.text_input(f"Your answer (A/B/C/D) for Q{i+1}", key=f"ai_ans_{i}")
            st.session_state.ai_answers[i] = ans.strip().upper()

        if st.button("Submit Quiz Answers"):
            user_answers = st.session_state.ai_answers
            quiz_eval_text = json.dumps({"quiz": quiz, "answers": user_answers})
            evaluation = gemini_api(f"Evaluate answers and provide score, wrong questions, and weak topics: {quiz_eval_text}")
            st.success("Quiz Evaluation:")
            st.text(evaluation)

            # Update progress
            try:
                score_line = [line for line in evaluation.split("\n") if "score" in line.lower()]
                score = int(score_line[0].split(":")[1].strip().split("/")[0])
            except:
                score = 0
            progress = load_progress(progress_file)
            progress["history"].append({"date": str(date.today()), "score": score})
            assign_badges(progress, score)
            save_progress(progress_file, progress)
            display_badges(progress)

# -------------------- VOICE TO NOTES --------------------
def run_voice_to_notes(username):
    st.header("🎙️ Voice to Notes")
    audio_file = st.file_uploader("Upload lecture audio (MP3/WAV/M4A)", type=["mp3","wav","m4a"])
    transcription = ""

    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(audio_file.read())
            temp_path = temp.name
        st.info("Transcribing audio... please wait")
        transcription = gemini_api(f"Transcribe lecture audio {temp_path} into concise study notes")
        st.success("Transcription complete:")
        st.text_area("Transcript", transcription, height=150)
        os.remove(temp_path)

    if transcription:
        if st.button("Generate Quiz from Notes"):
            quiz_text = gemini_api(f"Generate 5 multiple-choice questions (A-D) from transcript:\n{transcription} in JSON without answers")
            try:
                st.session_state.voice_quiz = json.loads(quiz_text)
                st.session_state.voice_answers = {}
            except:
                st.error("Failed to generate quiz.")

        voice_quiz = st.session_state.get("voice_quiz", [])
        if voice_quiz:
            st.subheader("📝 Answer the Voice Notes Quiz")
            for i, q in enumerate(voice_quiz):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                for idx, opt in enumerate(q['options']):
                    st.markdown(f"{chr(65+idx)}. {opt}")
                ans = st.text_input(f"Your answer (A/B/C/D) for Q{i+1}", key=f"voice_ans_{i}")
                st.session_state.voice_answers[i] = ans.strip().upper()

            if st.button("Submit Voice Quiz Answers"):
                user_answers = st.session_state.voice_answers
                quiz_eval_text = json.dumps({"quiz": voice_quiz, "answers": user_answers})
                evaluation = gemini_api(f"Evaluate answers and provide score, wrong questions, and weak topics: {quiz_eval_text}")
                st.success("Quiz Evaluation:")
                st.text(evaluation)

                # Update progress
                try:
                    score_line = [line for line in evaluation.split("\n") if "score" in line.lower()]
                    score = int(score_line[0].split(":")[1].strip().split("/")[0])
                except:
                    score = 0
                progress_file = f"{username}_progress.json"
                progress = load_progress(progress_file)
                progress["history"].append({"date": str(date.today()), "score": score})
                assign_badges(progress, score)
                save_progress(progress_file, progress)
                display_badges(progress)

# -------------------- DASHBOARD --------------------
def show_dashboard(username):
    st.header("📊 Study Progress Dashboard")
    progress_file = f"{username}_progress.json"
    progress = load_progress(progress_file)
    history = progress.get("history", [])
    if not history:
        st.warning("No quiz data yet. Take a quiz first!")
        return
    df = pd.DataFrame(history)

    # Latest score bar
    latest_score = df.iloc[-1]["score"]
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width:{latest_score}%;"></div>
    </div>
    <p style='color:#1b5e20;'>Latest Quiz Score: {latest_score}%</p>
    """, unsafe_allow_html=True)

    # Progress line chart
    st.subheader("📈 Progress Over Time")
    plt.figure()
    plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
    plt.xlabel("Date")
    plt.ylabel("Score (%)")
    plt.title("Quiz Score Progress")
    st.pyplot(plt)

    # Pie chart: correct vs wrong
    st.subheader("🥧 Quiz Performance Analytics")
    summary = progress.get("summary",{})
    labels = ["Correct","Wrong"]
    values = [summary.get("correct",0), summary.get("wrong",0)]
    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#66bb6a","#ef5350"])
    plt.title("Overall Quiz Analytics")
    st.pyplot(plt)

    # Badges
    st.subheader("🏅 Badges Earned")
    display_badges(progress)
