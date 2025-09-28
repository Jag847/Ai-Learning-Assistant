import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
from database import save_quiz_result, get_quiz_results
from fpdf import FPDF
import tempfile
import os

# -------------------- AI CALL FUNCTION --------------------
def generate_ai_response(prompt):
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }

    try:
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Error: {e}"

# -------------------- QUIZ GENERATION FROM FILE --------------------
def generate_quiz_from_file(file):
    """Generates quiz questions and answers from uploaded file using AI."""
    file_content = file.read().decode("utf-8", errors="ignore") if hasattr(file, 'read') else ""
    prompt = f"Generate a quiz with questions and answers based on the following content:\n{file_content}\nFormat as JSON: {{'question': '', 'options': [], 'answer': '', 'topic': ''}}"
    ai_response = generate_ai_response(prompt)

    try:
        import json
        quiz = json.loads(ai_response)
        if isinstance(quiz, dict):
            quiz = [quiz]
        return quiz
    except Exception:
        st.warning("AI did not return valid JSON. Using fallback quiz.")
        # Fallback sample quiz
        return [
            {"question": "Sample Question?", "options": ["A", "B", "C", "D"], "answer": "A", "topic": "Sample"}
        ]

# -------------------- QUIZ FUNCTION --------------------
def run_quiz(user_id):
    st.subheader("📝 AI-Powered Quiz")

    # Upload file option
    uploaded_file = st.file_uploader("Upload a PDF/TXT/DOCX to generate quiz:", type=["pdf", "txt", "docx"])
    quiz_data = st.session_state.get("quiz_data", None)

    if uploaded_file:
        with st.spinner("Generating quiz from file..."):
            quiz_data = generate_quiz_from_file(uploaded_file)
            st.session_state.quiz_data = quiz_data
            st.success("✅ Quiz generated!")

    if not quiz_data:
        st.info("Upload a file or enter text in AI Study Buddy to generate quiz.")
        return

    # Store answers
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    # Display questions dynamically
    for i, q in enumerate(quiz_data):
        st.markdown(f"**Q{i+1}: {q['question']}**")
        if q.get("options"):
            for option in q["options"]:
                if st.button(option, key=f"{i}_{option}"):
                    st.session_state.quiz_answers[i] = option
        else:
            ans = st.text_input(f"Answer for Q{i+1}", key=f"input_{i}")
            if ans:
                st.session_state.quiz_answers[i] = ans
        st.markdown("---")

    # Submit
    if st.button("📤 Submit Quiz"):
        score = 0
        for i, q in enumerate(quiz_data):
            if str(st.session_state.quiz_answers.get(i)).strip().lower() == str(q["answer"]).strip().lower():
                score += 1

        st.success(f"✅ You scored {score}/{len(quiz_data)}")
        save_quiz_result(user_id, score, len(quiz_data))

        # AI-generated weak topics analysis
        weak_topics = [q.get("topic", "General") for i, q in enumerate(quiz_data)
                       if str(st.session_state.quiz_answers.get(i)).strip().lower() != str(q["answer"]).strip().lower()]
        if weak_topics:
            prompt = f"Provide detailed tips and areas to improve for the following topics: {', '.join(weak_topics)}"
            insights = generate_ai_response(prompt)
            st.markdown("### 🔍 Areas to Improve:")
            st.write(insights)
        else:
            st.success("🎉 Excellent! All answers correct.")

        st.experimental_rerun()


# -------------------- DEVELOPMENT / PROGRESS --------------------
def show_progress(user_id):
    st.subheader("📊 Your Development")
    results = get_quiz_results(user_id)
    if not results:
        st.info("No quiz data yet. Take a quiz first!")
        return

    df = pd.DataFrame(results, columns=["Score", "Total", "Timestamp"])
    df["Attempt"] = range(1, len(df) + 1)

    # Animated line chart
    fig_line = px.line(df, x="Attempt", y="Score", title="Quiz Score Progress", markers=True, line_shape="spline")
    st.plotly_chart(fig_line, use_container_width=True)

    # Pie chart of last attempt
    last_score = df.iloc[-1]
    correct = last_score["Score"]
    wrong = last_score["Total"] - correct
    fig_pie = px.pie(names=["Correct", "Incorrect"], values=[correct, wrong],
                     title="Last Quiz Results", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

    # Option to download charts + quiz as PDF
    if st.button("💾 Download Quiz Report as PDF"):
        pdf_file = create_pdf_report(df, st.session_state.get("quiz_data", []), last_score)
        st.download_button("Download PDF", data=open(pdf_file, "rb").read(), file_name="quiz_report.pdf", mime="application/pdf")
        os.remove(pdf_file)

def create_pdf_report(df, quiz_data, last_score):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "📊 Quiz Report", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Latest Score: {last_score['Score']}/{last_score['Total']}", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, "Quiz Questions and Answers:", ln=True)
    for i, q in enumerate(quiz_data):
        pdf.multi_cell(0, 8, f"Q{i+1}: {q['question']}\nAnswer: {q['answer']}\n")
        pdf.ln(1)

    # Save charts as images
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    return tmp_file.name
