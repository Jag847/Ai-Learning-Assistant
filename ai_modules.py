import streamlit as st
import requests
import json
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import re

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

# -------------------- SAFE JSON PARSE --------------------
def safe_json_loads(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return []
    return []

# -------------------- PROGRESS STORAGE --------------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "summary": {"correct":0,"wrong":0,"weak":0}, "badges":[]}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

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
        badge_html = ""
        for b in badges:
            badge_html += f"<div class='badge'>{b}</div>"
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.info("No badges earned yet.")

# -------------------- AI STUDY BUDDY --------------------
def run_ai_study_buddy():
    st.header("🧠 AI Study Buddy")
    
    # Ask question feature
    question = st.text_input("Ask a question or topic:")
    if st.button("Get Answer"):
        if question:
            answer = gemini_api(f"Answer this academic question clearly: {question}")
            st.success(answer)
        else:
            st.warning("Enter a question!")

    # Quiz generation
    st.subheader("🎯 Quiz Time")
    topic = st.text_input("Enter quiz topic:")
    if st.button("Generate Quiz"):
        prompt = f"""
        Generate 5 multiple-choice questions (MCQs) on the topic '{topic}'.
        Each question should have:
          - "question": The question text
          - "options": List of 4 options labeled a,b,c,d
          - "answer": The correct option letter (a/b/c/d)
          - "topic": Key topic
        Respond ONLY with valid JSON array.
        """
        quiz_text = gemini_api(prompt)
        st.session_state.quiz_data = safe_json_loads(quiz_text)
        if not st.session_state.quiz_data:
            st.error("Failed to generate quiz. Try another topic.")

    # Take quiz
    quiz_data = st.session_state.get("quiz_data", [])
    if quiz_data:
        st.subheader("📝 Take the Quiz")
        user_answers = []
        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            options = q.get("options", [])
            selected = st.radio(f"Select an answer for Q{i+1}", options, key=f"q{i}")
            user_answers.append(selected)
        if st.button("Submit Answers"):
            score = 0
            weak_topics = []
            for i, q in enumerate(quiz_data):
                if user_answers[i].lower() == q.get("answer","").lower():
                    score += 1
                else:
                    weak_topics.append(q.get("topic","General"))
            st.success(f"✅ Score: {score}/{len(quiz_data)}")
            if weak_topics:
                st.info(f"Weak Topics: {', '.join(set(weak_topics))}")
                tips = gemini_api(f"Provide tips to improve in: {', '.join(set(weak_topics))}")
                st.write(tips)

            # Save progress
            progress = load_progress()
            new_score = int(score/len(quiz_data)*100)
            progress["history"].append({"date": str(date.today()), "score": new_score})
            progress["summary"]["correct"] += score
            progress["summary"]["wrong"] += len(quiz_data) - score
            progress["summary"]["weak"] += len(set(weak_topics))
            assign_badges(progress, new_score)
            save_progress(progress)
            display_badges(progress)
