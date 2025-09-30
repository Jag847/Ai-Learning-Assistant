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
def load_progress(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {"history": [], "summary": {"correct":0,"wrong":0,"weak":0}}

def save_progress(file, progress):
    with open(file, "w") as f:
        json.dump(progress, f, indent=4)

def reset_progress(file):
    if os.path.exists(file):
        os.remove(file)

# -------------------- AI STUDY QUIZ --------------------
def run_ai_quiz():
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
        st.session_state.quiz_answers = {}

    topic = st.text_input("Enter a quiz topic (AI Study Buddy):")
    if st.button("Generate Quiz"):
        quiz_json = gemini_api(
            f"Create 5 multiple-choice questions on {topic} with 4 options each in JSON format with keys: question, options, answer, topic."
        )
        try:
            st.session_state.quiz_data = json.loads(quiz_json)
        except:
            st.error("Failed to generate quiz. Please try another topic.")

    quiz_data = st.session_state.quiz_data
    if quiz_data:
        st.subheader("📝 Take the Quiz")
        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            options = q.get("options", [])
            labeled_options = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(options)]
            selected = st.radio(f"Select for Q{i+1}", labeled_options, key=f"q{i}")
            if selected:
                st.session_state.quiz_answers[i] = selected.split(". ", 1)[1]

        if st.button("Submit Answers"):
            score, weak_topics = 0, []
            for i, q in enumerate(quiz_data):
                user_ans = st.session_state.quiz_answers.get(i, "")
                if user_ans.lower() == q.get("answer", "").lower():
                    score += 1
                else:
                    weak_topics.append(q.get("topic", "General"))
            st.success(f"✅ Score: {score}/{len(quiz_data)}")
            if weak_topics:
                st.info(f"Weak Topics: {', '.join(set(weak_topics))}")
                tips = gemini_api(f"Provide tips to improve in: {', '.join(set(weak_topics))}")
                st.write(tips)

# -------------------- VOICE TO NOTES & QUIZ --------------------
def run_voice_quiz():
    st.subheader("🎙️ Voice to Notes")

    # Upload audio
    uploaded_file = st.file_uploader("Upload lecture audio (MP3/WAV/M4A):", type=["mp3","wav","m4a"])
    transcription = ""
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(uploaded_file.read())
            temp_path = temp.name
        st.info("Transcribing audio...")
        transcription = gemini_api(f"Transcribe this audio into concise study notes.")
        st.success("Transcription complete:")
        st.text_area("Transcript", transcription, height=150)
        os.remove(temp_path)

    # Live microphone (optional)
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with st.expander("Use Live Microphone (local only)"):
            if st.button("Start Listening"):
                with sr.Microphone() as source:
                    st.info("Listening... speak now")
                    audio_data = r.listen(source)
                    transcription = r.recognize_google(audio_data)
                    st.text_area("Live Transcript", transcription, height=150)
    except Exception:
        st.warning("Live microphone input not available on this system.")

    # Quiz from transcript
    if transcription:
        if st.button("Generate Quiz from Transcript"):
            quiz_json = gemini_api(
                f"Generate 5 multiple-choice questions from this text:\n{transcription} in JSON format with keys: question, options, answer, topic"
            )
            try:
                st.session_state.voice_quiz = json.loads(quiz_json)
            except:
                st.error("Failed to generate quiz.")

        voice_quiz = st.session_state.get("voice_quiz", [])
        if voice_quiz:
            st.subheader("📝 Take Voice-to-Notes Quiz")
            if "quiz_answers" not in st.session_state:
                st.session_state.quiz_answers = {}
            for i, q in enumerate(voice_quiz):
                st.markdown(f"**Q{i+1}: {q.get('question','')}**")
                options = q.get("options", [])
                labeled_options = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(options)]
                selected = st.radio(f"Select for Q{i+1}", labeled_options, key=f"v_q{i}")
                if selected:
                    st.session_state.quiz_answers[i] = selected.split(". ",1)[1]

            if st.button("Submit Voice Quiz Answers"):
                score, weak_topics = 0, []
                for i, q in enumerate(voice_quiz):
                    user_ans = st.session_state.quiz_answers.get(i,"")
                    if user_ans.lower() == q.get("answer","").lower():
                        score += 1
                    else:
                        weak_topics.append(q.get("topic","General"))
                st.success(f"✅ Score: {score}/{len(voice_quiz)}")
                if weak_topics:
                    st.info(f"Weak Topics: {', '.join(set(weak_topics))}")
                    tips = gemini_api(f"Provide tips to improve in: {', '.join(set(weak_topics))}")
                    st.write(tips)
