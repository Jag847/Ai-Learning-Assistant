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
    return {"history": [], "summary":{"correct":0,"wrong":0}, "badges":[]}

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

    # -------------------- ASK QUESTION --------------------
    question = st.text_input("Ask a question or topic:")
    if st.button("Get Answer"):
        if question:
            answer = gemini_api(f"Answer this academic question clearly: {question}")
            st.success(answer)
        else:
            st.warning("Enter a question!")

    # -------------------- QUIZ GENERATION --------------------
    st.subheader("🎯 Quiz Time")
    topic = st.text_input("Enter quiz topic for AI-generated quiz:")
    if st.button("Generate Quiz"):
        raw_quiz = gemini_api(
            f"Generate 5 multiple-choice questions on '{topic}'. "
            "Return only JSON array with 5 objects. Each object must have: "
            "'question' (string), 'options' (array of 4 strings), 'topic' (string). "
            "Do NOT include answers or explanations."
        )
        try:
            st.session_state.quiz_data = json.loads(raw_quiz)
            st.session_state.quiz_answers = {}
            st.success("Quiz generated successfully! Fill your answers below.")
        except json.JSONDecodeError:
            st.error("Failed to generate quiz. Please try another topic.")
            st.text_area("API Output (Debug)", raw_quiz, height=200)

    # -------------------- QUIZ ANSWER INPUT --------------------
    quiz_data = st.session_state.get("quiz_data", [])
    if quiz_data:
        st.subheader("📝 Submit Your Answers")
        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            user_ans = st.text_input(f"Your answer for Q{i+1} (A/B/C/D):", key=f"user_ans_{i}")
            st.session_state.quiz_answers[i] = user_ans.strip().upper()

        if st.button("Submit Answers"):
            if not st.session_state.quiz_answers:
                st.warning("Please answer all questions before submitting.")
            else:
                # Get correct answers from Gemini API
                answer_prompt = "Provide only JSON array of correct answers in order (A/B/C/D) for these questions:\n"
                answer_prompt += json.dumps(quiz_data)
                correct_ans_raw = gemini_api(answer_prompt)
                try:
                    correct_answers = json.loads(correct_ans_raw)
                except:
                    st.error("Failed to fetch correct answers. Try submitting again.")
                    st.text_area("API Output (Debug)", correct_ans_raw, height=200)
                    return

                # Calculate score and weak topics
                score = 0
                weak_topics = []
                for i, q in enumerate(quiz_data):
                    user_ans = st.session_state.quiz_answers.get(i,"")
                    correct_ans = correct_answers[i].upper()
                    if user_ans == correct_ans:
                        score += 1
                    else:
                        weak_topics.append(q.get("topic","General"))

                # Show result
                st.success(f"✅ Score: {score}/{len(quiz_data)}")
                if weak_topics:
                    st.info(f"Weak Topics: {', '.join(set(weak_topics))}")
                    tips = gemini_api(f"Provide tips to improve in: {', '.join(set(weak_topics))}")
                    st.write(tips)

                # Update progress and badges
                progress = load_progress()
                progress["history"].append({"date": str(date.today()), "score": int(score/len(quiz_data)*100)})
                progress["summary"]["correct"] += score
                progress["summary"]["wrong"] += len(quiz_data)-score
                progress["summary"]["weak"] += len(set(weak_topics))
                assign_badges(progress, int(score/len(quiz_data)*100))
                save_progress(progress)
                display_badges(progress)
# -------------------- VOICE TO NOTES --------------------
def run_voice_to_notes():
    st.header("🎙️ Voice to Notes")

    transcription = ""
    audio_file = st.file_uploader("Upload lecture audio (MP3/WAV/M4A):", type=["mp3","wav","m4a"])

    # -------------------- AUDIO UPLOAD --------------------
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(audio_file.read())
            temp_path = temp.name
        st.info("Transcribing audio... please wait")
        transcription = gemini_api(f"Transcribe this uploaded lecture audio into concise study notes.")
        st.success("Transcription complete:")
        st.text_area("Transcript", transcription, height=150)
        os.remove(temp_path)

    # -------------------- LIVE SPEECH (if local) --------------------
    if st.checkbox("Use Microphone for Live Notes (Local Only)"):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("Listening... speak now.")
                audio_data = r.listen(source)
                transcription = r.recognize_google(audio_data)
                st.text_area("Live Transcript", transcription, height=150)
        except Exception as e:
            st.error(f"Live microphone input not available: {e}")

    # -------------------- GENERATE QUIZ FROM TRANSCRIPT --------------------
    if transcription and st.button("Generate Quiz from Transcript"):
        raw_quiz = gemini_api(
            f"Generate 5 multiple-choice questions from this transcript:\n{transcription}\n"
            "Return only JSON array with 5 objects. Each object must have: "
            "'question' (string), 'options' (array of 4 strings), 'topic' (string). "
            "Do NOT include answers or explanations."
        )
        try:
            st.session_state.voice_quiz = json.loads(raw_quiz)
            st.session_state.quiz_answers = {}
            st.success("Quiz generated! Fill your answers below.")
        except:
            st.error("Failed to generate quiz. Try another transcript or topic.")
            st.text_area("API Output (Debug)", raw_quiz, height=200)

    # -------------------- QUIZ ANSWER INPUT --------------------
    voice_quiz = st.session_state.get("voice_quiz", [])
    if voice_quiz:
        st.subheader("📝 Submit Your Answers")
        for i, q in enumerate(voice_quiz):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            user_ans = st.text_input(f"Your answer for Q{i+1} (A/B/C/D):", key=f"v_user_ans_{i}")
            st.session_state.quiz_answers[i] = user_ans.strip().upper()

        if st.button("Submit Voice Quiz Answers"):
            if not st.session_state.quiz_answers:
                st.warning("Please answer all questions before submitting.")
            else:
                # Get correct answers from Gemini API
                answer_prompt = "Provide only JSON array of correct answers in order (A/B/C/D) for these questions:\n"
                answer_prompt += json.dumps(voice_quiz)
                correct_ans_raw = gemini_api(answer_prompt)
                try:
                    correct_answers = json.loads(correct_ans_raw)
                except:
                    st.error("Failed to fetch correct answers. Try submitting again.")
                    st.text_area("API Output (Debug)", correct_ans_raw, height=200)
                    return

                # Calculate score and weak topics
                score = 0
                weak_topics = []
                for i, q in enumerate(voice_quiz):
                    user_ans = st.session_state.quiz_answers.get(i,"")
                    correct_ans = correct_answers[i].upper()
                    if user_ans == correct_ans:
                        score += 1
                    else:
                        weak_topics.append(q.get("topic","General"))

                # Show results
                st.success(f"✅ Score: {score}/{len(voice_quiz)}")
                if weak_topics:
                    st.info(f"Weak Topics: {', '.join(set(weak_topics))}")
                    tips = gemini_api(f"Provide tips to improve in: {', '.join(set(weak_topics))}")
                    st.write(tips)

                # Update progress and badges
                progress = load_progress()
                progress["history"].append({"date": str(date.today()), "score": int(score/len(voice_quiz)*100)})
                progress["summary"]["correct"] += score
                progress["summary"]["wrong"] += len(voice_quiz)-score
                progress["summary"]["weak"] += len(set(weak_topics))
                assign_badges(progress, int(score/len(voice_quiz)*100))
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

    # Line chart
    st.subheader("📈 Progress Over Time")
    plt.figure()
    plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
    plt.xlabel("Date")
    plt.ylabel("Score (%)")
    plt.title("Quiz Score Progress")
    st.pyplot(plt)

    # Pie chart without weak topics
    st.subheader("🥧 Quiz Performance Analytics")
    summary = progress.get("summary",{})
    labels = ["Correct","Wrong"]
    values = [summary.get("correct",0), summary.get("wrong",0)]
    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#66bb6a","#ef5350"])
    plt.title("Overall Quiz Analytics")
    st.pyplot(plt)

    # Display badges
    st.subheader("🏅 Badges Earned")
    display_badges(progress)
