import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from ai_modules import gemini_api, generate_quiz, check_quiz_answers, load_progress, save_progress, reset_progress

PROGRESS_FILE = "user_progress.json"
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
body {background-color: #e8f5e9;}
.sidebar .sidebar-content {background-color: #c8e6c9;}
.stButton>button {background-color: #2e7d32;color:white;border-radius:8px;}
.stButton>button:hover {background-color:#1b5e20;}
</style>
""", unsafe_allow_html=True)

progress = load_progress(PROGRESS_FILE)

# ---------------- NAVIGATION ----------------
st.sidebar.title("🌿 Navigation")
page = st.sidebar.radio("Go to", ["Welcome", "AI Study Buddy", "Voice to Notes", "Progress Dashboard", "Settings / Logout"])

# ---------------- WELCOME ----------------
if page == "Welcome":
    st.markdown("<h1 style='color:#2e7d32;'>Let's take a step towards a better Earth 🌍</h1>", unsafe_allow_html=True)
    if st.button("🚀 Let's Get Started"):
        st.experimental_rerun()

# ---------------- AI STUDY BUDDY ----------------
elif page == "AI Study Buddy":
    st.header("🧠 AI Study Buddy")
    topic = st.text_input("Enter a quiz topic (AI Study Buddy):")
    
    if st.button("Generate Quiz") and topic:
        st.session_state.quiz = generate_quiz(topic)
        st.session_state.user_answers = {}

    quiz = st.session_state.get("quiz", [])
    if quiz:
        st.subheader("📝 Quiz Questions")
        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            for j, opt in enumerate(q.get("options", [])):
                st.radio(f"Select for Q{i+1}", q["options"], key=f"q{i}", index=0)
        
        st.subheader("Enter your answers in sequence (e.g., A,B,C,D):")
        ans_input = st.text_input("Your Answers:", key="ans_input")

        if st.button("Submit Answers") and ans_input:
            user_answers_list = [a.strip().upper() for a in ans_input.split(",")]
            user_answers = {i: quiz[i]["options"][ord(user_answers_list[i])-65] for i in range(len(user_answers_list))}
            result = check_quiz_answers(quiz, user_answers)
            
            score = sum(1 for r in result if r.get("is_correct"))
            st.success(f"✅ Score: {score}/{len(quiz)}")
            for r in result:
                if not r.get("is_correct"):
                    st.info(f"Question: {r['question']}\nCorrect Answer: {r['correct_answer']}\nTopic to Improve: {r['topic_to_improve']}")

            # Update progress
            progress["history"].append({"date": str(date.today()), "score": score})
            progress["summary"]["correct"] += score
            progress["summary"]["wrong"] += len(quiz)-score
            save_progress(PROGRESS_FILE, progress)

# ---------------- VOICE TO NOTES ----------------
elif page == "Voice to Notes":
    st.header("🎙️ Voice to Notes")
    st.write("Upload lecture audio and optionally use live microphone (local only).")
    uploaded_file = st.file_uploader("Upload audio (MP3/WAV/M4A):", type=["mp3","wav","m4a"])
    transcription = ""
    if uploaded_file:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(uploaded_file.read())
            temp_path = temp.name
        st.info("Transcribing...")
        transcription = gemini_api(f"Transcribe this audio into concise study notes.")
        st.text_area("Transcript", transcription, height=150)
    
    if transcription:
        if st.button("Generate Quiz from Transcript"):
            st.session_state.voice_quiz = generate_quiz(transcription)
    
    quiz = st.session_state.get("voice_quiz", [])
    if quiz:
        st.subheader("📝 Voice-to-Notes Quiz")
        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            for opt in q.get("options", []):
                st.radio(f"Select for Q{i+1}", q["options"], key=f"v_q{i}", index=0)
        ans_input = st.text_input("Enter answers in sequence (e.g., A,B,C,D):", key="voice_ans_input")
        if st.button("Submit Voice Answers") and ans_input:
            user_answers_list = [a.strip().upper() for a in ans_input.split(",")]
            user_answers = {i: quiz[i]["options"][ord(user_answers_list[i])-65] for i in range(len(user_answers_list))}
            result = check_quiz_answers(quiz, user_answers)
            
            score = sum(1 for r in result if r.get("is_correct"))
            st.success(f"✅ Score: {score}/{len(quiz)}")
            for r in result:
                if not r.get("is_correct"):
                    st.info(f"Question: {r['question']}\nCorrect Answer: {r['correct_answer']}\nTopic to Improve: {r['topic_to_improve']}")

# ---------------- PROGRESS DASHBOARD ----------------
elif page == "Progress Dashboard":
    st.header("📊 Study Progress")
    if not progress["history"]:
        st.warning("No progress data available yet.")
    else:
        df = pd.DataFrame(progress["history"])
        st.subheader("📈 Progress Over Time")
        plt.figure()
        plt.plot(df["date"], df["score"], marker="o", color="#2e7d32")
        plt.xlabel("Date")
        plt.ylabel("Score (%)")
        st.pyplot(plt)

        st.subheader("🥧 Quiz Performance")
        summary = progress["summary"]
        labels = ["Correct", "Wrong"]
        values = [summary["correct"], summary["wrong"]]
        plt.figure()
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#66bb6a","#ef5350"])
        st.pyplot(plt)

# ---------------- SETTINGS ----------------
elif page == "Settings / Logout":
    st.header("⚙️ Settings")
    if st.button("Reset Progress Data"):
        reset_progress(PROGRESS_FILE)
        st.success("Progress reset successfully!")
