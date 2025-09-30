import streamlit as st
import json
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import random

# ---------------- CONFIG ----------------
PROGRESS_FILE = "user_progress.json"
USERS_FILE = "users.json"

# ---------------- PROGRESS STORAGE ----------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE,"r") as f:
            return json.load(f)
    return {"history": [], "summary":{"correct":0,"wrong":0}, "badges":[]}

def save_progress(progress):
    with open(PROGRESS_FILE,"w") as f:
        json.dump(progress,f,indent=4)

# ---------------- BADGES ----------------
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
        html = "".join([f"<div class='badge'>{b}</div>" for b in badges])
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No badges earned yet.")

# ---------------- USERS ----------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE,"r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE,"w") as f:
        json.dump(users,f,indent=4)

def signup_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists!"
    users[username] = {"password": password}
    save_users(users)
    return True, "Signup successful!"

def login_user(username, password):
    users = load_users()
    if username in users and users[username]["password"] == password:
        return True
    return False

# ---------------- SAMPLE QUIZ GENERATOR ----------------
def generate_quiz(topic):
    # Mock quiz generation: 5 questions with options and answers
    questions = [
        {
            "question": f"What is a key concept in {topic}?",
            "options": ["Option A","Option B","Option C","Option D"],
            "answer": random.choice(["A","B","C","D"])
        } for _ in range(5)
    ]
    return questions

# ---------------- AI STUDY BUDDY ----------------
def run_ai_study_buddy():
    st.header("🧠 AI Study Buddy")
    topic = st.text_input("Enter quiz topic:")
    
    if st.button("Generate Quiz"):
        st.session_state.quiz_data = generate_quiz(topic)
        st.session_state.user_answers = {}

    if "quiz_data" in st.session_state:
        st.subheader("📝 Take the Quiz")
        for idx, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{idx+1}: {q['question']}**")
            ans = st.radio(f"Choose an option for Q{idx+1}", q["options"], key=f"ans{idx}")
            st.session_state.user_answers[idx] = ans[0]  # store first letter as answer

        if st.button("Submit Answers"):
            correct = 0
            wrong = 0
            weak_topics = []
            for idx, q in enumerate(st.session_state.quiz_data):
                if st.session_state.user_answers.get(idx) == q["answer"]:
                    correct += 1
                else:
                    wrong += 1
                    weak_topics.append(q["question"])
            score = int((correct/len(st.session_state.quiz_data))*100)
            
            progress = load_progress()
            progress["history"].append({"date": str(date.today()), "score": score})
            progress["summary"]["correct"] += correct
            progress["summary"]["wrong"] += wrong
            assign_badges(progress, score)
            save_progress(progress)
            
            st.success(f"✅ You scored {score}% ({correct} correct, {wrong} wrong)")
            display_badges(progress)
            if weak_topics:
                st.info(f"Topics to improve: {', '.join(weak_topics)}")

# ---------------- VOICE TO NOTES ----------------
def run_voice_to_notes():
    st.header("🎙️ Voice to Notes")
    audio_file = st.file_uploader("Upload lecture audio", type=["mp3","wav","m4a"])
    transcription = ""
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(audio_file.read())
            temp_path = temp.name
        transcription = f"Transcribed content of {audio_file.name} (mocked)"  # placeholder
        st.text_area("Transcript", transcription, height=150)
        os.remove(temp_path)
    if transcription and st.button("Generate Quiz from Notes"):
        st.session_state.voice_quiz = generate_quiz("Lecture Notes")

# ---------------- DASHBOARD ----------------
def show_dashboard():
    st.header("📊 Study Progress Dashboard")
    progress = load_progress()
    history = progress.get("history", [])
    if not history:
        st.warning("No quiz data yet. Take a quiz first!")
        return
    df = pd.DataFrame(history)
    latest_score = df.iloc[-1]["score"]
    st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width:{latest_score}%;'></div></div><p>Latest Score: {latest_score}%</p>", unsafe_allow_html=True)
    
    st.subheader("📈 Progress Over Time")
    plt.figure()
    plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
    plt.xlabel("Date")
    plt.ylabel("Score (%)")
    st.pyplot(plt)

    st.subheader("🥧 Quiz Performance")
    summary = progress.get("summary",{})
    labels = ["Correct","Wrong"]
    values = [summary.get("correct",0), summary.get("wrong",0)]
    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=["#66bb6a","#ef5350"])
    st.pyplot(plt)
    
    st.subheader("🏅 Badges Earned")
    display_badges(progress)
