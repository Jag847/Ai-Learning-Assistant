import streamlit as st 
import requests
import json
import os
import re
import base64
import PyPDF2
from datetime import date

API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# -------------------- PROGRESS FILE --------------------
def get_progress_file(username):
    return f"{username}_progress.json"

# -------------------- FILE HANDLING --------------------
def process_file(uploaded_file):
    if uploaded_file is None:
        return None
    if uploaded_file.type == "application/pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = "".join([page.extract_text() + "\n" for page in pdf_reader.pages])
            return {"text": text.strip()}
        except Exception as e:
            st.error(f"Failed to read PDF: {e}")
            return None
    elif uploaded_file.type.startswith("image/"):
        data = base64.b64encode(uploaded_file.read()).decode("utf-8")
        mime = uploaded_file.type
        return {"inline_data": {"mime_type": mime, "data": data}}
    return None

# -------------------- GEMINI API --------------------
def gemini_api(prompt: str, file_data=None):
    parts = [{"text": prompt}]
    if file_data:
        if "text" in file_data:
            parts[0]["text"] += "\n\nDocument content:\n" + file_data["text"]
        elif "inline_data" in file_data:
            parts.append(file_data["inline_data"])

    data = {"contents": [{"parts": parts}]}
    headers = {"Content-Type": "application/json"}

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
        try:
            with open(file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("Corrupted progress file. Resetting progress.")
            return {
                "history": [],
                "summary": {"correct": 0, "wrong": 0},
                "badges": [],
                "chat_history": [],
                "flashcards": [],
                "quizzes": []     
            }
    return {
        "history": [],
        "summary": {"correct": 0, "wrong": 0},
        "badges": [],
        "chat_history": [],
        "flashcards": [],
        "quizzes": []         
    }

def save_progress(username, progress):
    with open(get_progress_file(username), "w") as f:
        json.dump(progress, f, indent=4)

# -------------------- BADGES --------------------
def assign_badges(progress):
    badges = progress.get("badges", [])
    if len(progress.get("flashcards", [])) >= 3 and "📚 Flashcard Master" not in badges:
        badges.append("📚 Flashcard Master")
    if len(progress.get("quizzes", [])) >= 3 and "🧩 Quiz Challenger" not in badges:
        badges.append("🧩 Quiz Challenger")
    progress["badges"] = badges

def display_badges(progress):
    badges = progress.get("badges", [])
    if badges:
        badge_html = "".join([f"<div class='badge'>{b}</div>" for b in badges])
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.info("No badges earned yet.")

# -------------------- PROGRESS DASHBOARD --------------------
def show_dashboard(username):
    st.header("📊 Progress Dashboard")
    progress = load_progress(username)

    st.subheader("Flashcard Usage")
    if progress["flashcards"]:
        st.write(f"Total Flashcard Sets: {len(progress['flashcards'])}")
        topics = [fc["topic"] for fc in progress["flashcards"]]
        st.write(f"Topics Covered: {', '.join(set(topics))}")
    else:
        st.info("No flashcards generated yet.")

    st.subheader("Quiz History")
    if progress.get("quizzes"):
        st.write(f"Total Quizzes: {len(progress['quizzes'])}")
        topics = [q["topic"] for q in progress["quizzes"]]
        st.write(f"Topics Covered: {', '.join(set(topics))}")
    else:
        st.info("No quizzes generated yet.")

    st.subheader("Badges Earned")
    display_badges(progress)

# -------------------- CLEAN JSON HELPERS --------------------
def extract_json_from_text(text):
    """Extract JSON block safely from raw LLM output."""
    json_match = re.search(r"\[.*\]", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            return None
    return None

# -------------------- AI STUDY BUDDY --------------------
def run_ai_study_buddy(username):
    progress = load_progress(username)
    st.header("🧠 AI Study Buddy")

    # ---------- Q&A ----------
    st.subheader("❓ Ask a Question")
    uploaded_file_qa = st.file_uploader("Upload PDF/Image (optional)", type=["pdf", "png", "jpg", "jpeg"], key="qa_upload")
    question = st.text_input("Enter your academic question:")
    if st.button("Get Answer"):
        if not question:
            st.warning("Enter a question!")
        else:
            answer = gemini_api(f"Answer clearly and simply: {question}", process_file(uploaded_file_qa))
            st.success(answer)
            progress["chat_history"].append({
                "type": "Question",
                "content": question,
                "answer": answer,
                "timestamp": str(date.today())
            })
            save_progress(username, progress)

    # ---------- QUIZ ----------
    st.subheader("🎯 Quiz Time")
    uploaded_file_quiz = st.file_uploader("Upload PDF/Image for quiz (optional)", type=["pdf", "png", "jpg", "jpeg"], key="quiz_upload")
    topic = st.text_input("Enter quiz topic:")
    num_questions = st.slider("Number of questions", 5, 20, 10)

    if st.button("Generate Quiz"):
        content = topic.strip()
        file_data = process_file(uploaded_file_quiz)
        if file_data:
            content = gemini_api("Summarize content for quiz generation:", file_data)

        if not content:
            st.warning("Provide a topic or file.")
        else:
            quiz_prompt = (
                f"Generate {num_questions} multiple-choice questions on '{content}'. "
                "Each question should have 4 options labeled A, B, C, D, and then list the correct answers clearly at the end."
            )
            quiz_text = gemini_api(quiz_prompt)
            st.session_state.quiz_text = quiz_text

            # Save quiz to progress
            progress["quizzes"].append({
                "topic": topic or "Untitled",
                "num_questions": num_questions,
                "content": quiz_text,
                "timestamp": str(date.today())
            })
            progress["chat_history"].append({
                "type": "Quiz",
                "content": topic or "Untitled",
                "num_questions": num_questions,
                "timestamp": str(date.today())
            })
            assign_badges(progress)
            save_progress(username, progress)

            st.success(f"Generated {num_questions} quiz questions on '{topic}'!")

    if "quiz_text" in st.session_state:
        st.subheader("📝 Quiz Questions")
        text = st.session_state.quiz_text
        # Split questions and answers
        parts = re.split(r"(?:Answers|Correct Answers)[:\-]", text, flags=re.IGNORECASE)
        questions_part = parts[0].strip() if parts else text
        answers_part = parts[1].strip() if len(parts) > 1 else None

        st.markdown("### Questions:")
        st.text_area("Quiz Content", value=questions_part, height=400)

        if answers_part:
            with st.expander("View Answers"):
                st.text_area("Answers", value=answers_part, height=300)

        if st.button("Clear Quiz"):
            del st.session_state.quiz_text
            st.success("Quiz cleared!")

    # ---------- FLASHCARDS ----------
    st.subheader("📚 Flashcards")
    flashcard_topic = st.text_input("Enter topic for flashcards:")
    num_cards = st.slider("Number of flashcards", 1, 10, 5)

    if st.button("Generate Flashcards"):
        if not flashcard_topic:
            st.warning("Enter a topic!")
        else:
            flashcard_prompt = (
                f"Generate {num_cards} flashcards for topic '{flashcard_topic}'. "
                "Each should have a 'Front:' and 'Back:' clearly labeled."
            )
            flash_text = gemini_api(flashcard_prompt)
            cards = re.findall(r"Front:(.*?)Back:(.*?)(?=Front:|$)", flash_text, re.DOTALL)
            if cards:
                flashcards = [{"front": f.strip(), "back": b.strip()} for f, b in cards]
                st.session_state.flashcards = flashcards
                progress["flashcards"].append({
                    "topic": flashcard_topic,
                    "cards": flashcards,
                    "timestamp": str(date.today())
                })
                progress["chat_history"].append({
                    "type": "Flashcards",
                    "content": flashcard_topic,
                    "num_cards": num_cards,
                    "timestamp": str(date.today())
                })
                assign_badges(progress)
                save_progress(username, progress)
                st.success(f"Generated {len(flashcards)} flashcards!")
            else:
                st.error("Failed to parse flashcards. Try again.")

    if "flashcards" in st.session_state:
        st.subheader("Practice Flashcards")
        for i, card in enumerate(st.session_state.flashcards):
            if f"flip_{i}" not in st.session_state:
                st.session_state[f"flip_{i}"] = False
            if st.button(f"Card {i+1}: Show {'Back' if not st.session_state[f'flip_{i}'] else 'Front'}", key=f"flip_{i}_btn"):
                st.session_state[f"flip_{i}"] = not st.session_state[f"flip_{i}"]
            st.info(card["back"] if st.session_state[f"flip_{i}"] else card["front"])

        if st.button("Clear Flashcards"):
            del st.session_state.flashcards
            st.success("Flashcards cleared!")
