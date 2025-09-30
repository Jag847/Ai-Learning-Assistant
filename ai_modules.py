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

# -------------------- PROGRESS --------------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "summary":{"correct":0,"wrong":0,"weak":0}, "badges":[],"quiz_records":[]}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

def reset_progress():
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

# -------------------- BADGES --------------------
def assign_badges(progress, score):
    badges = progress.get("badges", [])
    if score >= 80 and "🌟 High Scorer" not in badges:
        badges.append("🌟 High Scorer")
    if len(progress.get("history", [])) >= 5 and "🔥 Consistent Learner" not in badges:
        badges.append("🔥 Consistent Learner")
    if len(progress.get("history", [])) == 1 and "🎯 First Quiz Completed" not in badges:
        badges.append("🎯 First Quiz Completed")
    progress["badges"] = badges

def display_badges(progress):
    badges = progress.get("badges", [])
    if badges:
        badge_html = "".join([f"<div class='badge'>{b}</div>" for b in badges])
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.info("No badges earned yet.")

# -------------------- INTERACTIVE QUIZ HELPER --------------------
def interactive_quiz(quiz_text, progress):
    """
    Generates an interactive quiz from quiz_text (JSON or structured string)
    """
    import ast
    try:
        quiz_data = ast.literal_eval(quiz_text)
        if isinstance(quiz_data, dict):
            quiz_data = [quiz_data]
    except Exception:
        # fallback sample
        quiz_data = [{"question":"Sample Q?","options":["A","B","C","D"],"answer":"A","topic":"General"}]

    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    for idx, q in enumerate(quiz_data):
        st.markdown(f"**Q{idx+1}: {q['question']}**")
        if q.get("options"):
            for opt in q["options"]:
                if st.button(opt, key=f"{idx}_{opt}"):
                    st.session_state.quiz_answers[idx] = opt
                    st.experimental_rerun()
        else:
            ans = st.text_input(f"Answer Q{idx+1}", key=f"input_{idx}", value=st.session_state.quiz_answers.get(idx, ""))
            if ans:
                st.session_state.quiz_answers[idx] = ans
        st.markdown("---")

    if st.button("Submit Quiz"):
        correct_count = sum(
            1 for i,q in enumerate(quiz_data)
            if str(st.session_state.quiz_answers.get(i,"")).strip().lower() == str(q["answer"]).strip().lower()
        )
        wrong_count = len(quiz_data) - correct_count
        weak_topics = [q.get("topic","General") for i,q in enumerate(quiz_data)
                       if str(st.session_state.quiz_answers.get(i,"")).strip().lower() != str(q["answer"]).strip().lower()]

        st.success(f"✅ Score: {correct_count}/{len(quiz_data)}")
        if weak_topics:
            insights = gemini_api(f"Provide improvement tips for: {', '.join(weak_topics)}")
            st.markdown("### 🔍 Areas to Improve")
            st.write(insights)

        # Save progress
        new_score = int(correct_count / len(quiz_data) * 100)
        progress["history"].append({"date": str(date.today()), "score": new_score})
        progress["summary"]["correct"] += correct_count
        progress["summary"]["wrong"] += wrong_count
        progress["summary"]["weak"] += len(weak_topics)
        assign_badges(progress,new_score)
        save_progress(progress)
        display_badges(progress)
        st.session_state.quiz_answers = {}

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
        quiz_text = gemini_api(f"Generate 5 quiz questions with 4 options each on {topic}. Include correct answer.")
        progress = load_progress()
        interactive_quiz(quiz_text, progress)

# -------------------- VOICE TO NOTES --------------------
def run_voice_to_notes():
    st.header("🎙️ Voice to Notes")
    audio_file = st.file_uploader("Upload lecture audio", type=["mp3","wav","m4a"])
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(audio_file.read())
            temp_path = temp.name

        st.info("Transcribing... please wait")
        transcription = gemini_api(f"Convert this audio into detailed summarized study notes.")
        st.success(transcription)

        if st.button("Generate Quiz from Notes"):
            quiz_text = gemini_api(f"Generate 5 interactive quiz questions based on these notes:\n{transcription}")
            progress = load_progress()
            interactive_quiz(quiz_text, progress)

        if st.button("Summarize Notes"):
            summary = gemini_api(f"Summarize the following notes:\n{transcription}")
            st.markdown(summary)

        os.remove(temp_path)

# -------------------- DASHBOARD --------------------
def show_dashboard():
    st.header("📊 Study Progress Dashboard")
    progress = load_progress()
    history = progress.get("history", [])
    if not history:
        st.warning("No quiz data yet.")
        return

    df = pd.DataFrame(history)
    latest_score = df.iloc[-1]["score"]

    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width:{latest_score}%;"></div>
    </div>
    <p style='color:#1b5e20;'>Latest Quiz Score: {latest_score}%</p>
    """, unsafe_allow_html=True)

    # Line chart
    st.subheader("📈 Progress Over Time")
    plt.figure()
    plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
    plt.xlabel("Date")
    plt.ylabel("Score (%)")
    plt.title("Quiz Score Progress")
    st.pyplot(plt)

    # Pie chart
    st.subheader("🥧 Quiz Performance Analytics")
    summary = progress.get("summary", {})
    labels = ["Correct","Wrong","Weak Topics"]
    values = [summary.get("correct",0), summary.get("wrong",0), summary.get("weak",0)]
    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#66bb6a","#ef5350","#ffee58"])
    plt.title("Overall Quiz Analytics")
    st.pyplot(plt)

    # Badges
    st.subheader("🏅 Badges Earned")
    display_badges(progress)
