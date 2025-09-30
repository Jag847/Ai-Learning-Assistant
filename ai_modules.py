import streamlit as st
import requests
import json
import os
import tempfile
from datetime import date

API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# ---------------- GEMINI API ----------------
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

# ---------------- PROGRESS ----------------
def load_progress(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {"history": [], "summary": {"correct":0,"wrong":0}}

def save_progress(file, progress):
    with open(file, "w") as f:
        json.dump(progress, f, indent=4)

def reset_progress(file):
    if os.path.exists(file):
        os.remove(file)

# ---------------- AI QUIZ ----------------
def generate_quiz(topic, n_questions=5):
    """
    Generate multiple-choice quiz questions (without answers) using Gemini API.
    """
    prompt = (
        f"Create {n_questions} multiple-choice questions on '{topic}' with 4 options each, "
        "in JSON format with keys: question, options. Do NOT include answers."
    )
    result = gemini_api(prompt).replace("\n","")
    try:
        quiz = json.loads(result)
        return quiz
    except:
        return []

def check_quiz_answers(quiz, user_answers):
    """
    Ask Gemini API for the correct answers and key topics for improvement.
    """
    # Prepare questions with user answers
    qa_pairs = []
    for i, q in enumerate(quiz):
        ans = user_answers.get(i, "")
        qa_pairs.append({"question": q["question"], "user_answer": ans, "options": q["options"]})
    
    prompt = (
        "Given the following quiz questions and the user's answers, provide correct answers, "
        "mark wrong answers, and key topics to improve. Return JSON format with keys: question, "
        "user_answer, correct_answer, is_correct, topic_to_improve.\n"
        f"Data: {json.dumps(qa_pairs)}"
    )
    result = gemini_api(prompt).replace("\n","")
    try:
        return json.loads(result)
    except:
        return []
