import streamlit as st
import requests
import json
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

API_KEY = "YOUR_API_KEY"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# -------------------- PROGRESS FILE --------------------
def get_progress_file(username):
    return f"{username}_progress.json"

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
def load_progress(username):
    file = get_progress_file(username)
    if os.path.exists(file):
        with open(file,"r") as f:
            return json.load(f)
    return {"history": [], "summary":{"correct":0,"wrong":0}, "badges":[]}

def save_progress(username, progress):
    file = get_progress_file(username)
    with open(file,"w") as f:
        json.dump(progress,f,indent=4)

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

# -------------------- AI STUDY BUDDY --------------------
def run_ai_study_buddy(username):
    progress = load_progress(username)
    st.header("🧠 AI Study Buddy")
    
    # ---------- Q&A ----------
    question = st.text_input("Ask a question or topic:")
    if st.button("Get Answer"):
        if question:
            answer = gemini_api(f"Answer this academic question clearly: {question}")
            st.success(answer)
        else:
            st.warning("Enter a question!")

    # ---------- Quiz ----------
    st.subheader("🎯 Quiz Time")
    topic = st.text_input("Enter quiz topic:")
    if st.button("Generate Quiz"):
        quiz_text = gemini_api(f"Generate 5 multiple-choice questions on '{topic}' without answers in JSON format, include 'question' and 'options' fields")
        try:
            st.session_state.quiz_data = json.loads(quiz_text)
            st.success("Quiz generated! Enter your answers below.")
            st.session_state.user_answers = {}
        except:
            st.error("Failed to generate quiz. Try another topic.")

    # Display quiz questions and input answers
    if "quiz_data" in st.session_state:
        st.subheader("📝 Answer the Quiz")
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            ans = st.text_input(f"Your answer for Q{i+1}:", key=f"ans{i}")
            st.session_state.user_answers[i] = ans

        if st.button("Submit Quiz Answers"):
            # Evaluate answers using Gemini API
            correct = 0
            weak_topics = []
            for i, q in enumerate(st.session_state.quiz_data):
                user_ans = st.session_state.user_answers.get(i, "")
                check_prompt = f"Is the following answer correct for the question?\nQuestion: {q['question']}\nOptions: {q['options']}\nAnswer: {user_ans}\nRespond with 'correct' or 'wrong' and specify topic if wrong."
                result = gemini_api(check_prompt).lower()
                if "correct" in result:
                    correct += 1
                else:
                    weak_topics.append(q.get("topic","General"))

            wrong = len(st.session_state.quiz_data) - correct
            st.success(f"✅ Correct: {correct}, ❌ Wrong: {wrong}")
            if weak_topics:
                st.info(f"Focus on improving: {', '.join(set(weak_topics))}")
                tips = gemini_api(f"Provide improvement tips for: {', '.join(set(weak_topics))}")
                st.write(tips)

            # Save progress
            score = int((correct / len(st.session_state.quiz_data)) * 100)
            progress["history"].append({"date": str(date.today()), "score": score})
            progress["summary"]["correct"] += correct
            progress["summary"]["wrong"] += wrong
            assign_badges(progress, score)
            save_progress(username, progress)
            display_badges(progress)
