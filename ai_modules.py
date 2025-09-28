import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px


# -------------------- AI CALL FUNCTION --------------------
def generate_ai_response(prompt):
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300
        }
    }

    try:
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Error: {e}"


# -------------------- QUIZ DATA --------------------
# Example questions, replace with dynamic AI-generated quiz if needed
quiz_questions = [
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "Paris", "Rome", "Madrid"],
        "answer": "Paris",
        "topic": "Geography"
    },
    {
        "question": "What is 7 x 8?",
        "options": ["54", "56", "64", "58"],
        "answer": "56",
        "topic": "Math"
    },
    {
        "question": "Which gas do plants absorb?",
        "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
        "answer": "Carbon Dioxide",
        "topic": "Biology"
    }
]

# -------------------- APP FUNCTIONS --------------------
def run_quiz():
    st.subheader("📝 Take the Quiz")
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    for i, q in enumerate(quiz_questions):
        st.markdown(f"**Q{i+1}: {q['question']}**")
        for option in q["options"]:
            if st.button(option, key=f"{i}_{option}"):
                st.session_state.quiz_answers[i] = option
        st.markdown("---")

    if st.button("📤 Submit Quiz"):
        score = sum(1 for i, q in enumerate(quiz_questions)
                    if st.session_state.quiz_answers.get(i) == q["answer"])
        st.session_state.last_score = score
        st.success(f"✅ You scored {score}/{len(quiz_questions)}")
        store_score(score)
        st.experimental_rerun()


def store_score(score):
    if "scores" not in st.session_state:
        st.session_state.scores = []
    st.session_state.scores.append(score)


def show_progress():
    st.subheader("📊 Your Development")
    if "scores" not in st.session_state or len(st.session_state.scores) == 0:
        st.info("No quiz data yet. Take a quiz first!")
        return

    # Score progress over time
    df = pd.DataFrame({"Attempt": list(range(1, len(st.session_state.scores)+1)),
                       "Score": st.session_state.scores})
    fig_line = px.line(df, x="Attempt", y="Score", title="Quiz Score Progress",
                       markers=True, line_shape="spline")
    st.plotly_chart(fig_line, use_container_width=True)

    # Pie chart of last quiz
    if "last_score" in st.session_state:
        correct = st.session_state.last_score
        wrong = len(quiz_questions) - correct
        fig_pie = px.pie(names=["Correct", "Incorrect"], values=[correct, wrong],
                         title="Last Quiz Results", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # AI insights for improvement
    weak_topics = [q["topic"] for i, q in enumerate(quiz_questions)
                   if st.session_state.quiz_answers.get(i) != q["answer"]]
    if weak_topics:
        prompt = f"Provide learning tips and improvements for the following topics: {', '.join(weak_topics)}"
        insights = generate_ai_response(prompt)
        st.markdown("### 🔍 Areas to Improve:")
        st.write(insights)
    else:
        st.success("🎉 Excellent! You got all questions right.")


# -------------------- MAIN APP INTERFACE --------------------
def run_ai_learning_assistant(username: str):
    # -------------------- PAGE STYLE --------------------
    st.markdown("""
    <style>
    @keyframes slideIn {from {opacity: 0; transform: translateX(80px);}to {opacity: 1; transform: translateX(0);}}
    .stApp {background-image: linear-gradient(to bottom right, #a8e063, #56ab2f);background-size: cover;background-position: center;color: #2e7d32;animation: slideIn 0.9s ease-out;}
    .assistant-box {background-color: rgba(255,255,255,0.92);padding: 2.5rem;border-radius: 20px;max-width: 900px;margin: auto;margin-top: 3rem;text-align: center;box-shadow: 0 8px 28px rgba(0,0,0,0.25);animation: slideIn 1.1s ease-out;}
    .stTextInput > div > div > input {border: 2px solid #81c784;border-radius: 12px;padding: 10px;font-size: 1rem;}
    .stButton > button {background-color: #43a047 !important;color: white !important;font-size: 1.05rem;border-radius: 10px;padding: 0.6rem 1.8rem;font-weight: 600;transition: all 0.3s ease;box-shadow: 0 4px 12px rgba(67,160,71,0.4);}
    .stButton > button:hover {background-color: #2e7d32 !important;transform: scale(1.05);box-shadow: 0 6px 18px rgba(46,125,50,0.6);}
    .response-box {background-color: #f1f8e9;padding: 1rem;border-radius: 12px;margin-top: 1rem;border: 1px solid #c5e1a5;text-align: left;color: #33691e;animation: slideIn 0.8s ease-out;}
    </style>
    """, unsafe_allow_html=True)

    # -------------------- HEADER --------------------
    st.markdown("<div class='assistant-box'>", unsafe_allow_html=True)
    st.title(f"🎓 Welcome {username}, Your AI Learning Assistant is Ready!")
    st.sidebar.header("📚 Navigation")
    menu = st.sidebar.radio("Choose a tool", ["AI Study Buddy", "Lecture Voice-to-Notes", "Your Development"])
    st.markdown("<hr>", unsafe_allow_html=True)

    # -------------------- AI STUDY BUDDY --------------------
    if menu == "AI Study Buddy":
        st.subheader("🧩 AI Study Buddy — Understand & Revise Smarter")
        text = st.text_area("Enter topic or material:", height=200)
        task = st.selectbox("Choose an action:", ["Explain in simple terms", "Summarize", "Generate quiz", "Create flashcards"])
        if st.button("✨ Generate"):
            if text.strip():
                with st.spinner("⚙️ AI is working..."):
                    time.sleep(1.0)
                    result = generate_ai_response(f"{task} this content:\n{text}")
                st.markdown("<div class='response-box'>", unsafe_allow_html=True)
                st.success("✅ Result:")
                st.write(result)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("Please enter some text.")

    # -------------------- VOICE TO NOTES --------------------
    elif menu == "Lecture Voice-to-Notes":
        st.subheader("🎤 Lecture Voice-to-Notes Generator")
        file = st.file_uploader("Upload Lecture Audio (mp3/wav)", type=["mp3", "wav"])
        if file:
            st.audio(file)
            st.info("Simulating transcription... (Replace with Whisper/Speech API)")
            transcription = "Photosynthesis is the process by which green plants convert light energy..."
            st.markdown("<div class='response-box'>", unsafe_allow_html=True)
            st.write("🗒️ Transcribed Text:")
            st.write(transcription)
            st.markdown("</div>", unsafe_allow_html=True)

            action = st.selectbox("Generate:", ["Summary", "Quiz", "Flashcards"])
            if st.button("🚀 Generate Notes"):
                with st.spinner("⚙️ Generating..."):
                    time.sleep(1.0)
                    result = generate_ai_response(f"{action} based on: {transcription}")
                st.markdown("<div class='response-box'>", unsafe_allow_html=True)
                st.success("✅ Generated:")
                st.write(result)
                st.markdown("</div>", unsafe_allow_html=True)

    # -------------------- YOUR DEVELOPMENT --------------------
    elif menu == "Your Development":
        show_progress()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Welcome"):
        st.session_state["page"] = "welcome"
        st.session_state["transition"] = "fade"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
