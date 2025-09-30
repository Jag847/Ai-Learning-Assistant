import streamlit as st
import requests
import json
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# -------------------- CONFIG --------------------
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
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "summary": {"correct":0,"wrong":0}, "badges":[]}

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
    # Ask a question
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
    if st.button("Generate Quiz Questions"):
        quiz_text = gemini_api(f"Generate 5 multiple-choice questions with 4 options each on {topic} in JSON format without answers, include topic field")
        try:
            st.session_state.quiz_questions = json.loads(quiz_text)
        except:
            st.error("Failed to generate quiz. Try another topic.")
            st.session_state.quiz_questions = []

    # Display quiz and collect user answers
    quiz_questions = st.session_state.get("quiz_questions", [])
    if quiz_questions:
        st.subheader("📝 Answer the Quiz")
        if "user_answers" not in st.session_state:
            st.session_state.user_answers = {}

        for i, q in enumerate(quiz_questions):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            options = q.get("options", [])
            st.session_state.user_answers[i] = st.text_input(f"Your Answer for Q{i+1}:", key=f"ans_{i}")

        if st.button("Submit Quiz"):
            # Send user answers to Gemini API to get correct/wrong and weak topics
            answers_payload = {
                "questions": quiz_questions,
                "user_answers": st.session_state.user_answers
            }
            result_text = gemini_api(f"Check the following quiz answers and return: score out of total, correct/wrong per question, weak topics to improve.\nJSON format:\n{json.dumps(answers_payload)}")
            try:
                result = json.loads(result_text)
            except:
                st.error("Failed to evaluate answers. Check API response.")
                return

            score = result.get("score",0)
            weak_topics = result.get("weak_topics",[])

            st.success(f"✅ Your Score: {score}/{len(quiz_questions)}")
            if weak_topics:
                st.info(f"Weak Topics: {', '.join(set(weak_topics))}")
                tips = gemini_api(f"Provide tips to improve in: {', '.join(set(weak_topics))}")
                st.write(tips)

            # Update progress
            progress = load_progress()
            progress["history"].append({"date": str(date.today()), "score": score})
            progress["summary"]["correct"] += result.get("correct",0)
            progress["summary"]["wrong"] += result.get("wrong",0)
            assign_badges(progress, score)
            save_progress(progress)
            display_badges(progress)

# -------------------- VOICE TO NOTES --------------------
def run_voice_to_notes():
    st.header("🎙️ Voice to Notes")
    # File upload
    audio_file = st.file_uploader("Upload lecture audio (MP3/WAV/M4A):", type=["mp3","wav","m4a"])
    transcription = ""
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(audio_file.read())
            temp_path = temp.name
        st.info("Transcribing audio... please wait")
        transcription = gemini_api(f"Transcribe this audio into concise study notes")
        st.success("Transcription complete:")
        st.text_area("Transcript", transcription, height=150)
        os.remove(temp_path)

    # Live voice input (local only)
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening... speak now (local only)")
            audio_data = r.listen(source)
            live_text = r.recognize_google(audio_data)
            transcription += "\n" + live_text
            st.text_area("Live Transcript", transcription, height=150)
    except:
        st.info("Live microphone input not available in this environment.")

    # Quiz from transcript
    if transcription:
        if st.button("Generate Quiz from Transcript"):
            quiz_text = gemini_api(f"Generate 5 multiple-choice questions with 4 options each from this transcript in JSON without answers, include topic field:\n{transcription}")
            try:
                st.session_state.voice_quiz = json.loads(quiz_text)
            except:
                st.error("Failed to generate quiz.")

        voice_quiz = st.session_state.get("voice_quiz", [])
        if voice_quiz:
            st.subheader("📝 Answer Voice-to-Notes Quiz")
            if "voice_answers" not in st.session_state:
                st.session_state.voice_answers = {}

            for i, q in enumerate(voice_quiz):
                st.markdown(f"**Q{i+1}: {q.get('question','')}**")
                options = q.get("options", [])
                st.session_state.voice_answers[i] = st.text_input(f"Your Answer for Q{i+1}:", key=f"v_ans_{i}")

            if st.button("Submit Voice Quiz"):
                answers_payload = {
                    "questions": voice_quiz,
                    "user_answers": st.session_state.voice_answers
                }
                result_text = gemini_api(f"Check the following quiz answers and return: score out of total, correct/wrong per question, weak topics to improve.\nJSON format:\n{json.dumps(answers_payload)}")
                try:
                    result = json.loads(result_text)
                except:
                    st.error("Failed to evaluate answers.")
                    return

                score = result.get("score",0)
                weak_topics = result.get("weak_topics",[])

                st.success(f"✅ Your Score: {score}/{len(voice_quiz)}")
                if weak_topics:
                    st.info(f"Weak Topics: {', '.join(set(weak_topics))}")
                    tips = gemini_api(f"Provide tips to improve in: {', '.join(set(weak_topics))}")
                    st.write(tips)

                # Update progress
                progress = load_progress()
                progress["history"].append({"date": str(date.today()), "score": score})
                progress["summary"]["correct"] += result.get("correct",0)
                progress["summary"]["wrong"] += result.get("wrong",0)
                assign_badges(progress, score)
                save_progress(progress)
                display_badges(progress)

# -------------------- DASHBOARD --------------------
def show_dashboard():
    st.header("📊 Study Progress Dashboard")
    progress = load_progress()
    history = progress.get("history", [])
    if not history:
        st.warning("No quiz data yet. Take a quiz first!")
        return

    df = pd.DataFrame(history)
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

    # Pie chart Correct vs Wrong only
    st.subheader("🥧 Quiz Performance Analytics")
    summary = progress.get("summary", {})
    labels = ["Correct", "Wrong"]
    values = [summary.get("correct",0), summary.get("wrong",0)]
    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#66bb6a","#ef5350"])
    plt.title("Overall Quiz Analytics")
    st.pyplot(plt)

    # Floating badges
    st.subheader("🏅 Badges Earned")
    display_badges(progress)
