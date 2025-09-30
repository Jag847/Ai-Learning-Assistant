import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
from database import save_quiz_result, get_quiz_results
from fpdf import FPDF
import tempfile
import os
from streamlit_extras.let_it_rain import rain
import base64
import json
from datetime import datetime

# === Configure Gemini API (you already had this in your project) ===
API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# -------------------- INJECT CSS --------------------
def inject_css():
    st.markdown("""
    <style>
    @keyframes fadeIn {from {opacity:0;} to {opacity:1;}}
    @keyframes slideInRight {from {opacity:0; transform: translateX(80px);} to {opacity:1; transform: translateX(0);}}
    .stApp {animation: fadeIn 0.8s ease-out; background-image: linear-gradient(135deg,#a8e063,#56ab2f); color:#2e7d32; font-family:'Segoe UI',Tahoma,Verdana;}
    .stMetric {transition: transform 0.3s ease, box-shadow 0.3s ease; border-radius:12px;}
    .stMetric:hover {transform: scale(1.05); box-shadow: 0 8px 20px rgba(46,125,50,0.4);}
    .stButton>button {background: linear-gradient(90deg,#43a047,#66bb6a); color:white; font-size:1rem; font-weight:600; padding:0.6rem 1.5rem; border-radius:12px; border:none; transition: all 0.3s ease; box-shadow:0 4px 12px rgba(0,0,0,0.2);}
    .stButton>button:hover {transform: scale(1.05); box-shadow:0 6px 20px rgba(46,125,50,0.5); background: linear-gradient(90deg,#2e7d32,#43a047);}
    .stTextInput>div>div>input {border:2px solid #81c784; border-radius:10px; padding:10px; font-size:1rem; transition:border-color 0.3s ease, box-shadow 0.3s ease;}
    .stTextInput>div>div>input:focus {border-color:#2e7d32; box-shadow:0 0 10px rgba(46,125,50,0.4); outline:none;}
    .response-box {background-color: rgba(255,255,255,0.9); padding:1.8rem; border-radius:20px; margin-top:1rem; border-left:6px solid #43a047; box-shadow:0 8px 28px rgba(0,0,0,0.15); animation: slideInRight 0.8s ease-out;}
    .badge {display:inline-block; padding:0.4rem 0.8rem; margin:0.3rem; border-radius:12px; background: linear-gradient(135deg,#ffd700,#ffecb3); color:#4a4a4a; font-weight:700; box-shadow:0 4px 12px rgba(0,0,0,0.25); transition: transform 0.3s ease;}
    .badge:hover {transform: scale(1.2) rotate(-3deg); box-shadow:0 6px 20px rgba(0,0,0,0.35);}
    .stPlotlyChart>div {animation: fadeIn 1s ease-out;}
    </style>
    """, unsafe_allow_html=True)

# -------------------- Gemini call for text --------------------
def generate_ai_response(prompt, temperature=0.7, max_tokens=500):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
    }
    try:
        r = requests.post(URL, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        result = r.json()
        # Defensive parse
        return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    except Exception as e:
        return f"⚠️ Error: {e}"

# -------------------- Quiz generation (from text/file) --------------------
def generate_quiz_from_text(text):
    prompt = (
        "From the following content, generate a JSON array of multiple-choice questions "
        "with fields: question, options (4), answer (exact option text), topic. Use this format:\n"
        "[{'question':'','options':['','','',''],'answer':'','topic':''}, ...]\n\nCONTENT:\n" + text
    )
    out = generate_ai_response(prompt)
    try:
        quiz = json.loads(out)
        if isinstance(quiz, dict):
            quiz = [quiz]
        return quiz
    except Exception:
        # fallback: single sample
        return [{"question":"Sample Q?","options":["A","B","C","D"],"answer":"A","topic":"Sample"}]

def generate_quiz_from_file(file):
    # read file safely (pdf/txt/docx simple handling)
    try:
        data = file.read()
        if isinstance(data, bytes):
            try:
                text = data.decode('utf-8', errors='ignore')
            except Exception:
                text = ""
        else:
            text = str(data)
    except Exception:
        text = ""
    return generate_quiz_from_text(text if text else "No readable text found.")

# -------------------- Voice -> Notes (via Gemini text endpoint fallback) --------------------
def voice_to_notes_from_audiofile(audio_file):
    """
    Attempt to convert audio (bytes) to notes by:
     - Base64-encoding the audio and sending to Gemini with a transcription prompt.
    NOTE: Many text-generation endpoints won't accept raw audio as base64,
    so this is a fallback attempt. For robust transcription, use a dedicated STT endpoint.
    """
    try:
        audio_bytes = audio_file.read()
        b64 = base64.b64encode(audio_bytes).decode('ascii')
        # Construct prompt asking the model to transcribe base64-encoded audio.
        # If your Gemini supports speech input directly, replace this logic.
        prompt = (
            "You are a helpful assistant. Transcribe the following base64-encoded audio file and "
            "produce (1) a cleaned summarized lecture notes, (2) 5 multiple-choice quiz questions "
            "with answers and topics as JSON, and (3) a short list of weak topics to focus on.\n\n"
            f"BASE64_AUDIO:{b64}\n\nRespond in JSON: {{'notes':'','quiz':[],'weak_topics':[]}}"
        )
        out = generate_ai_response(prompt, temperature=0.0, max_tokens=800)
        try:
            parsed = json.loads(out)
            # ensure default keys
            parsed.setdefault("notes", "")
            parsed.setdefault("quiz", [])
            parsed.setdefault("weak_topics", [])
            if isinstance(parsed.get("quiz"), dict):
                parsed["quiz"] = [parsed["quiz"]]
            return parsed
        except Exception:
            # fallback: put transcript as notes and return sample quiz
            return {
                "notes": out[:5000],
                "quiz": [{"question":"Sample Q?","options":["A","B","C","D"],"answer":"A","topic":"Sample"}],
                "weak_topics": []
            }
    except Exception as e:
        return {"notes": f"⚠️ Error transcribing: {e}", "quiz": [], "weak_topics": []}

# -------------------- LIVE STATS / PIE CHART --------------------
def update_quiz_stats(return_fig=False):
    quiz_data = st.session_state.get("quiz_data", [])
    answers = st.session_state.get("quiz_answers", {})
    total_answered = len(answers)
    total_correct = sum(
        1
        for i, q in enumerate(quiz_data)
        if str(answers.get(i, "")).strip().lower() == str(q.get("answer", "")).strip().lower()
    )
    total_incorrect = total_answered - total_correct
    weak_topics = [
        q.get("topic", "General")
        for i, q in enumerate(quiz_data)
        if str(answers.get(i, "")).strip().lower() != str(q.get("answer", "")).strip().lower()
    ]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Correct", total_correct)
    col2.metric("❌ Incorrect", total_incorrect)
    col3.metric("📝 Answered", total_answered)
    col4.metric("🔍 Weak Topics", ", ".join(set(weak_topics)) if weak_topics else "None")

    fig = px.pie(names=["Correct", "Incorrect"], values=[total_correct, total_incorrect], hole=0.4,
                 title="Live Quiz Progress")
    st.plotly_chart(fig, use_container_width=True)
    if return_fig:
        return fig
    return fig

# -------------------- AI STUDY BUDDY (accepts safe_user dict) --------------------
def run_ai_learning_assistant(safe_user):
    """
    safe_user is a dict with at least keys: 'id' and 'username'
    """
    username = safe_user.get("username", "User")
    user_id = safe_user.get("id", 0)

    st.markdown(f"## 🎓 Welcome {username} — AI Learning Dashboard")
    inject_css()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 🧩 AI Study Buddy")
        text = st.text_area("Enter topic or material:", height=250)
        task = st.selectbox("Choose action:", ["Explain in simple terms", "Summarize", "Generate quiz", "Create flashcards"])
        if st.button("✨ Generate AI Content"):
            if text.strip():
                with st.spinner("⚙️ AI is working..."):
                    time.sleep(1)
                    result = generate_ai_response(f"{task} this content:\n{text}")
                st.success("✅ Result:")
                st.write(result)
            else:
                st.warning("Enter some text.")
    with col2:
        st.markdown("### 📝 Generate Quiz from File")
        uploaded_file = st.file_uploader("Upload PDF/TXT/DOCX:", type=["pdf", "txt", "docx"])
        if uploaded_file:
            with st.spinner("Generating quiz..."):
                st.session_state.quiz_data = generate_quiz_from_file(uploaded_file)
                st.success("✅ Quiz generated! Go to 'Take Quiz'.")
    st.markdown("### 📊 Live Stats")
    update_quiz_stats()
    col3, col4 = st.columns(2)
    with col3:
        if st.button("📚 Take Quiz"):
            st.session_state.page = "quiz"
            st.experimental_rerun()
    with col4:
        if st.button("📊 Your Development"):
            st.session_state.page = "development"
            st.experimental_rerun()

# -------------------- QUIZ --------------------
def run_quiz(user_id):
    st.subheader("📝 Take the Quiz")
    quiz_data = st.session_state.get("quiz_data", None)
    if not quiz_data:
        st.info("No quiz available.")
        return
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    # Present question-by-question and keep answers on per-question basis
    for i, q in enumerate(quiz_data):
        st.markdown(f"**Q{i+1}: {q.get('question','')}**")
        options = q.get("options", [])
        if options:
            # show radio to choose (ensures one answer per question)
            choice = st.radio(f"Select for Q{i+1}", options, index=options.index(st.session_state.quiz_answers.get(i, options[0])) if st.session_state.quiz_answers.get(i) in options else 0, key=f"radio_{i}")
            st.session_state.quiz_answers[i] = choice
        else:
            ans = st.text_input(f"Answer Q{i+1}", key=f"input_{i}", value=st.session_state.quiz_answers.get(i, ""))
            if ans:
                st.session_state.quiz_answers[i] = ans
        st.markdown("---")
        # show live progress after each question
        update_quiz_stats()

    if st.button("📤 Submit Quiz"):
        score = sum(
            1
            for i, q in enumerate(quiz_data)
            if str(st.session_state.quiz_answers.get(i, "")).strip().lower() == str(q.get("answer", "")).strip().lower()
        )
        st.success(f"✅ Score: {score}/{len(quiz_data)}")
        try:
            save_quiz_result(user_id, score, len(quiz_data))
        except Exception:
            # swallow DB save errors but continue
            st.warning("Could not save result to database.")
        weak_topics = [
            q.get("topic", "General")
            for i, q in enumerate(quiz_data)
            if str(st.session_state.quiz_answers.get(i, "")).strip().lower() != str(q.get("answer", "")).strip().lower()
        ]
        if weak_topics:
            insights = generate_ai_response(f"Provide tips to improve for: {', '.join(set(weak_topics))}")
            st.markdown("### 🔍 Areas to Improve")
            st.write(insights)
        else:
            st.success("🎉 Excellent! All correct.")
        if len(quiz_data) > 0 and score / len(quiz_data) >= 0.8:
            try:
                rain(emoji="🎉", font_size=30, falling_speed=5, animation_length=2)
            except Exception:
                pass
        # create PDF - we call helper
        try:
            fig_pie = update_quiz_stats(return_fig=True)
            pdf_file = create_pdf_report_with_chart(quiz_data, st.session_state.quiz_answers, weak_topics, fig_pie)
            with open(pdf_file, "rb") as fh:
                st.download_button("💾 Download Quiz PDF", data=fh.read(), file_name="quiz_report.pdf", mime="application/pdf")
            os.remove(pdf_file)
        except Exception:
            st.warning("Could not create PDF report.")
        display_badges(user_id, score)
        st.experimental_rerun()

# -------------------- PDF --------------------
def create_pdf_report_with_chart(quiz_data, answers, weak_topics, fig_pie):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "📊 Quiz Report", ln=True, align="C")
    pdf.ln(10)
    correct_count = sum(
        1
        for i, q in enumerate(quiz_data)
        if str(answers.get(i, "")).strip().lower() == str(q.get("answer", "")).strip().lower()
    )
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Score: {correct_count}/{len(quiz_data)}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, "Questions & Answers:", ln=True)
    pdf.ln(3)
    for i, q in enumerate(quiz_data):
        user_ans = answers.get(i, "")
        pdf.multi_cell(0, 8, f"Q{i+1}: {q.get('question','')}\nCorrect: {q.get('answer','')}\nYour Answer: {user_ans}\nTopic: {q.get('topic','General')}\n")
        pdf.ln(1)
    if weak_topics:
        pdf.cell(0, 10, "Weak Topics:", ln=True)
        pdf.multi_cell(0, 8, ", ".join(set(weak_topics)))
        pdf.ln(3)
    # export fig_pie to temporary png
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    try:
        # fig_pie is a plotly figure
        fig_pie.write_image(tmp_img.name)
        pdf.image(tmp_img.name, w=120)
    except Exception:
        pass
    tmp_img.close()
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)
    return tmp_pdf.name

# -------------------- BADGES --------------------
def display_badges(user_id, score):
    st.markdown("### 🏅 Earned Badges")
    badges = []
    try:
        results_len = len(get_quiz_results(user_id))
    except Exception:
        results_len = 0
    if results_len == 1:
        badges.append("🎯 First Quiz Completed")
    if "quiz_data" in st.session_state and len(st.session_state["quiz_data"]) > 0 and score / len(st.session_state["quiz_data"]) >= 0.8:
        badges.append("🌟 High Scorer")
    if results_len >= 5:
        badges.append("🔥 Consistent Learner")
    if badges:
        for b in badges:
            st.success(b)
    else:
        st.info("No new badges yet. Keep interacting!")

# -------------------- Development analytics helpers --------------------
def get_progress_figures(user_id):
    """
    Use get_quiz_results(user_id) to build:
      - time series (scores over timestamps)
      - pie chart of answered/correct/incorrect aggregated
    Returns tuple (fig_time, fig_pie)
    """
    try:
        rows = get_quiz_results(user_id)
    except Exception:
        rows = []
    if not rows:
        df = pd.DataFrame(columns=["score", "total", "timestamp"])
    else:
        df = pd.DataFrame(rows, columns=["score", "total", "timestamp"])
        # normalize timestamp if necessary
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        except Exception:
            # if timestamp is numeric or missing, create dummy
            df["timestamp"] = pd.date_range(end=pd.Timestamp.now(), periods=len(df))
    if len(df) == 0:
        fig_time = px.line(title="No quiz data")
        fig_pie = px.pie(names=["Correct"], values=[1], title="No data")
        return fig_time, fig_pie
    df["percentage"] = df["score"] / df["total"] * 100
    fig_time = px.line(df, x="timestamp", y="percentage", title="Quiz Scores Over Time", markers=True)
    total_correct = df["score"].sum()
    total_answered = df["total"].sum()
    total_incorrect = total_answered - total_correct
    fig_pie = px.pie(names=["Correct", "Incorrect"], values=[total_correct, total_incorrect], title="Overall Performance")
    return fig_time, fig_pie
