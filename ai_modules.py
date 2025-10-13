import streamlit as st 
import requests
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import base64
import PyPDF2

API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# -------------------- PROGRESS FILE --------------------
def get_progress_file(username):
    return f"{username}_progress.json"

# -------------------- PROCESS UPLOADED FILE --------------------
def process_file(uploaded_file):
    if uploaded_file is None:
        return None
    if uploaded_file.type == "application/pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return {"text": text.strip()}
        except:
            return None
    elif uploaded_file.type.startswith("image/"):
        data = base64.b64encode(uploaded_file.read()).decode("utf-8")
        mime = uploaded_file.type
        return {"inline_data": {"mime_type": mime, "data": data}}
    else:
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
                progress = json.load(f)
                # Ensure backward compatibility
                progress.setdefault("quizzes", [])
                progress.setdefault("flashcards", [])
                progress.setdefault("chat_history", [])
                progress.setdefault("badges", [])
                progress.setdefault("history", [])
                progress.setdefault("summary", {"correct": 0, "wrong": 0})
                return progress
        except json.JSONDecodeError:
            st.error("Corrupted progress file. Resetting progress.")
            return {
                "history": [],
                "summary": {"correct": 0, "wrong": 0},
                "badges": [],
                "chat_history": [],
                "flashcards": [],
                "quizzes": []  # ✅ Added to prevent KeyError
            }
    return {
        "history": [],
        "summary": {"correct": 0, "wrong": 0},
        "badges": [],
        "chat_history": [],
        "flashcards": [],
        "quizzes": []  # ✅ Added here too
    }

def save_progress(username, progress):
    file = get_progress_file(username)
    try:
        with open(file, "w") as f:
            json.dump(progress, f, indent=4)
    except Exception as e:
        st.error(f"Failed to save progress: {e}")

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
    
    st.subheader("Quiz Usage")
    if progress["quizzes"]:
        st.write(f"Total Quizzes Taken: {len(progress['quizzes'])}")
        topics = [q["topic"] for q in progress["quizzes"]]
        st.write(f"Quiz Topics: {', '.join(set(topics))}")
    else:
        st.info("No quizzes generated yet.")
    
    st.subheader("Badges Earned")
    display_badges(progress)

# -------------------- AI STUDY BUDDY --------------------
def run_ai_study_buddy(username):
    progress = load_progress(username)
    st.header("🧠 AI Study Buddy")
    
    # ---------- Q&A ----------
    st.subheader("❓ Ask a Question")
    uploaded_file_qa = st.file_uploader("Upload PDF or Image for context (optional)", type=["pdf", "png", "jpg", "jpeg"], key="qa_upload")
    question = st.text_input("Ask a question or topic:")
    if st.button("Get Answer"):
        if question:
            file_data = process_file(uploaded_file_qa)
            answer = gemini_api(f"Answer this academic question clearly in simple terms: {question}", file_data)
            st.success(answer)
            progress["chat_history"].append({
                "type": "Question",
                "content": question,
                "answer": answer,
                "timestamp": str(date.today())
            })
            save_progress(username, progress)
        else:
            st.warning("Enter a question!")

    # ---------- Quiz ----------
    st.subheader("🎯 Quiz Time")
    uploaded_file_quiz = st.file_uploader("Upload PDF or Image to generate quiz from (optional)", type=["pdf", "png", "jpg", "jpeg"], key="quiz_upload")
    topic = st.text_input("Enter quiz topic (or leave blank if using uploaded file):")
    num_questions = st.slider("Number of questions", 5, 20, 10)
    if st.button("Generate Quiz"):
        content = topic
        file_data = process_file(uploaded_file_quiz)
        if file_data:
            content = gemini_api("Summarize the key content from this document for quiz generation.", file_data)
        if not content:
            st.warning("Provide a topic or upload a file.")
        else:
            quiz_text = gemini_api(
                f"Generate {num_questions} multiple-choice questions on '{content}' "
                f"in JSON format as a list of objects, each with 'question', 'options' (4), and 'correct' (0-3)."
            )
            try:
                quiz_data = json.loads(quiz_text)
                st.session_state.quiz_data = quiz_data
                progress["quizzes"].append({
                    "topic": topic or "Uploaded Document",
                    "questions": quiz_data,
                    "timestamp": str(date.today())
                })
                assign_badges(progress)
                save_progress(username, progress)
                st.success(f"Quiz generated with {num_questions} questions!")
            except:
                st.error("Failed to generate quiz. Try another topic or file.")

    if "quiz_data" in st.session_state:
        st.subheader("📝 Quiz Questions")
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            for j, opt in enumerate(q['options']):
                st.write(f"{'ABCD'[j]}. {opt}")
            st.divider()

        with st.expander("Quiz Answers"):
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                st.write(f"✅ Correct: {'ABCD'[q['correct']]}. {q['options'][q['correct']]}")
                st.divider()

        if st.button("Clear Quiz"):
            del st.session_state.quiz_data
            st.success("Quiz cleared!")

    # ---------- Flashcards ----------
    st.subheader("📚 Flashcards")
    flashcard_topic = st.text_input("Enter topic for flashcards:")
    num_cards = st.slider("Number of flashcards", 1, 10, 5)
    if st.button("Generate Flashcards"):
        if flashcard_topic:
            flashcard_prompt = f"Generate {num_cards} flashcards on '{flashcard_topic}' in JSON format as a list of objects with 'front' and 'back'."
            flashcard_text = gemini_api(flashcard_prompt)
            try:
                flashcards = json.loads(flashcard_text)
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
            except:
                st.error("Failed to generate flashcards. Try another topic.")
        else:
            st.warning("Enter a topic!")

    if "flashcards" in st.session_state:
        st.subheader("Practice Flashcards")
        for i, card in enumerate(st.session_state.flashcards):
            with st.container():
                if f"flip_{i}" not in st.session_state:
                    st.session_state[f"flip_{i}"] = False
                if st.button(f"Card {i+1}: Show {'Back' if st.session_state[f'flip_{i}'] else 'Front'}", key=f"flip_btn_{i}"):
                    st.session_state[f"flip_{i}"] = not st.session_state[f"flip_{i}"]
                st.markdown(
                    f"<div class='flip-card {'flip-card-back' if st.session_state[f'flip_{i}'] else 'flip-card-front'}'>"
                    f"{card['back' if st.session_state[f'flip_{i}'] else 'front']}"
                    f"</div>",
                    unsafe_allow_html=True
                )
        if st.button("Clear Flashcards"):
            del st.session_state.flashcards
            st.success("Flashcards cleared!")
