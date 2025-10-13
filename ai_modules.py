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

# -------------------- PROCESS UPLOADED FILE --------------------
def process_file(uploaded_file):
    if uploaded_file is None:
        return None
    if uploaded_file.type == "application/pdf":
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += (page.extract_text() or "") + "\n"
            return {"text": text.strip()}
        except Exception as e:
            st.error(f"Failed to read PDF: {e}")
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
        response = requests.post(URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        # defensive access
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            # return full JSON as string if structure unexpected
            return json.dumps(result)
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
        topics = [q.get("topic", "Untitled") for q in progress["quizzes"]]
        st.write(f"Quiz Topics: {', '.join(set(topics))}")
    else:
        st.info("No quizzes generated yet.")
    
    st.subheader("Badges Earned")
    display_badges(progress)

# -------------------- QUIZ PARSING HELPERS --------------------
def try_parse_json_quiz(text):
    """Try to parse text as JSON quiz data (list of objects)."""
    try:
        obj = json.loads(text)
        # validate minimal structure
        if isinstance(obj, list) and all(isinstance(q, dict) for q in obj):
            # normalise keys
            parsed = []
            for q in obj:
                question = q.get("question") or q.get("prompt") or ""
                options = q.get("options") or q.get("choices") or []
                correct = q.get("correct")
                # if correct is label like 'A' convert to index
                if isinstance(correct, str) and correct.upper() in "ABCD":
                    correct = ord(correct.upper()) - ord('A')
                parsed.append({"question": question, "options": options, "correct": correct})
            return parsed
    except Exception:
        return None
    return None

def extract_json_substring(text):
    """Find JSON array substring in text and parse it."""
    matches = re.findall(r"\[.*\]", text, flags=re.DOTALL)
    for m in matches:
        parsed = try_parse_json_quiz(m)
        if parsed:
            return parsed
    return None

def parse_plain_text_quiz(text, expected_n=None):
    """
    Fallback parser: attempts to extract Q/A blocks from plain text.
    Returns list of {question, options(list), correct(index or None)}.
    """
    # common separators between questions: Q1, 1., Question 1, etc.
    # naive split into lines and group
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    questions = []
    current_q = None
    for line in lines:
        # question line heuristics
        if re.match(r'^(Q\s?\d+|Question\s?\d+|^\d+\.)', line, flags=re.IGNORECASE) or (len(line) > 20 and line.endswith('?')):
            # start new question
            if current_q:
                questions.append(current_q)
            # remove numbering prefix
            qtext = re.sub(r'^(Q\s?\d+|Question\s?\d+|^\d+\.)\s*', '', line, flags=re.IGNORECASE)
            current_q = {"question": qtext, "options": [], "correct": None}
            continue
        # options like A. text or (a) text
        m = re.match(r'^([A-Da-d])[\.\)]\s*(.*)', line)
        if m and current_q is not None:
            current_q["options"].append(m.group(2).strip())
            continue
        # lines like "Answer: B" or "Correct: A"
        m2 = re.match(r'^(Answer|Correct)[:\-]\s*([A-Da-d]|[0-3])', line, flags=re.IGNORECASE)
        if m2 and current_q is not None:
            ans = m2.group(2)
            if ans.isdigit():
                current_q["correct"] = int(ans)
            else:
                current_q["correct"] = ord(ans.upper()) - ord('A')
            continue
        # otherwise if current_q exists and no option pattern, maybe it's continuation of question
        if current_q and len(current_q["options"]) == 0 and len(current_q["question"]) < 200:
            # append as continuation
            current_q["question"] += " " + line
        elif current_q and len(current_q["options"]) > 0:
            # maybe option without A./B. prefix; append to last option
            current_q["options"][-1] += " " + line

    if current_q:
        questions.append(current_q)

    # If we couldn't find any questions but text looks like simple list, try splitting by double newlines into blocks
    if not questions:
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        for b in blocks:
            # attempt to extract question and four options
            parts = re.split(r'\n', b)
            if len(parts) >= 5:
                q = {"question": parts[0].strip(), "options": [p.strip() for p in parts[1:5]], "correct": None}
                # try detect "Answer:" in remainder
                for tail in parts[5:]:
                    m = re.search(r'Answer[:\-]\s*([A-Da-d0-3])', tail)
                    if m:
                        ans = m.group(1)
                        q["correct"] = int(ans) if ans.isdigit() else ord(ans.upper()) - ord('A')
                questions.append(q)

    # optionally limit to expected_n
    if expected_n and len(questions) > expected_n:
        questions = questions[:expected_n]

    return questions if questions else None

# -------------------- AI STUDY BUDDY --------------------
def run_ai_study_buddy(username):
    progress = load_progress(username)
    st.header("🧠 AI Study Buddy")

    # ---------- Q&A ----------
    st.subheader("❓ Ask a Question")
    uploaded_file_qa = st.file_uploader("Upload PDF or Image (optional)", type=["pdf", "png", "jpg", "jpeg"], key="qa_upload")
    question = st.text_input("Enter your academic question:", key="qa_question")
    if st.button("Get Answer"):
        if not question:
            st.warning("Enter a question!")
        else:
            answer = gemini_api(f"Answer clearly and simply: {question}", process_file(uploaded_file_qa))
            if isinstance(answer, str) and answer.startswith("⚠️ API Error"):
                st.error(answer)
            else:
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
    uploaded_file_quiz = st.file_uploader("Upload PDF or Image for quiz (optional)", type=["pdf", "png", "jpg", "jpeg"], key="quiz_upload")
    topic = st.text_input("Enter quiz topic (or leave blank if using uploaded file):", key="quiz_topic")
    num_questions = st.slider("Number of questions", 5, 20, 10, key="quiz_n")

    if st.button("Generate Quiz"):
        content = topic.strip()
        file_data = process_file(uploaded_file_quiz)
        if file_data:
            summary = gemini_api("Summarize the key content from this document for quiz generation.", file_data)
            # if API returned error string, surface it
            if isinstance(summary, str) and summary.startswith("⚠️ API Error"):
                st.error(summary)
                return
            content = summary or content

        if not content:
            st.warning("Provide a topic or upload a file.")
        else:
            # Stronger prompt with instruction to provide both plain text and JSON fallback
            quiz_prompt = (
                f"Generate {num_questions} multiple-choice questions on the following content. "
                "Output should include:\n\n"
                "1) A JSON array named 'quiz' where each item is an object with keys: 'question' (string), 'options' (list of 4 strings), 'correct' (0-3 integer).\n"
                "2) A human-readable section with questions labeled and answers at the end.\n\n"
                f"Content: {content}\n\n"
                "If you cannot output valid JSON, still provide the questions and answers in a clear readable format."
            )

            quiz_text = gemini_api(quiz_prompt)
            # check for API errors
            if isinstance(quiz_text, str) and quiz_text.startswith("⚠️ API Error"):
                st.error(quiz_text)
                return

            # Attempt parsing strategies (best → fallback)
            parsed = None
            parsed = try_parse_json_quiz(quiz_text)
            if not parsed:
                parsed = extract_json_substring(quiz_text)
            if not parsed:
                parsed = parse_plain_text_quiz(quiz_text, expected_n=num_questions)

            # If parsed as structured data, store normalized quiz_data
            if parsed:
                # ensure options length 4 and fill if needed
                for q in parsed:
                    opts = q.get("options", [])
                    if not isinstance(opts, list):
                        q["options"] = [str(opts)]
                    # pad/truncate to 4
                    if len(q["options"]) < 4:
                        # add placeholder options
                        while len(q["options"]) < 4:
                            q["options"].append("N/A")
                    elif len(q["options"]) > 4:
                        q["options"] = q["options"][:4]
                    # ensure correct is index or None
                    c = q.get("correct")
                    if isinstance(c, int):
                        if c < 0 or c >= 4:
                            q["correct"] = None
                    else:
                        q["correct"] = None
                st.session_state.quiz_data = parsed
                # Save both parsed structure and raw text
                progress["quizzes"].append({
                    "topic": topic or "Uploaded Document",
                    "questions": parsed,
                    "raw_text": quiz_text,
                    "timestamp": str(date.today())
                })
                progress["chat_history"].append({
                    "type": "Quiz",
                    "content": topic or "Uploaded Document",
                    "num_questions": len(parsed),
                    "timestamp": str(date.today())
                })
                assign_badges(progress)
                save_progress(username, progress)
                st.success(f"Quiz generated and parsed ({len(parsed)} questions).")
            else:
                # complete failure to parse — save raw text so user can inspect and retry manually
                st.error("Failed to parse quiz output into questions. Saved raw output to progress so you can inspect it.")
                progress["quizzes"].append({
                    "topic": topic or "Uploaded Document",
                    "questions": [],
                    "raw_text": quiz_text,
                    "timestamp": str(date.today())
                })
                progress["chat_history"].append({
                    "type": "Quiz",
                    "content": topic or "Uploaded Document",
                    "num_questions": 0,
                    "timestamp": str(date.today())
                })
                assign_badges(progress)
                save_progress(username, progress)
                # also store the raw output in session so user can see it
                st.session_state.quiz_text = quiz_text

    # Display quiz if structured
    if "quiz_data" in st.session_state:
        st.subheader("📝 Quiz Questions")
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            for j, opt in enumerate(q['options']):
                st.write(f"{'ABCD'[j]}. {opt}")
            st.divider()

        with st.expander("Quiz Answers"):
            for i, q in enumerate(st.session_state.quiz_data):
                correct = q.get("correct")
                if correct is None:
                    st.write(f"Q{i+1}: Correct answer not detected.")
                else:
                    st.write(f"Q{i+1}: {'ABCD'[correct]}. {q['options'][correct]}")
                st.divider()

        if st.button("Clear Quiz"):
            del st.session_state.quiz_data
            st.success("Quiz cleared!")

    # If we have raw quiz text (unparsed), show it and allow user to copy
    if "quiz_text" in st.session_state:
        st.subheader("🔎 Raw Quiz Output (unparsed)")
        st.text_area("Raw model output", value=st.session_state.quiz_text, height=400)
        if st.button("Clear Raw Quiz Output"):
            del st.session_state.quiz_text
            st.success("Cleared raw output.")

    # ---------- Flashcards ----------
    st.subheader("📚 Flashcards")
    flashcard_topic = st.text_input("Enter topic for flashcards:", key="fc_topic")
    num_cards = st.slider("Number of flashcards", 1, 10, 5, key="fc_n")
    if st.button("Generate Flashcards"):
        if flashcard_topic:
            flashcard_prompt = f"Generate {num_cards} flashcards on '{flashcard_topic}' in JSON format as a list of objects with 'front' and 'back'."
            flashcard_text = gemini_api(flashcard_prompt)
            if isinstance(flashcard_text, str) and flashcard_text.startswith("⚠️ API Error"):
                st.error(flashcard_text)
            else:
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
                except Exception:
                    # fallback: try to parse Front:/Back: format
                    cards = re.findall(r"Front:(.*?)Back:(.*?)(?=Front:|$)", flashcard_text or "", re.DOTALL)
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
                            "num_cards": len(flashcards),
                            "timestamp": str(date.today())
                        })
                        assign_badges(progress)
                        save_progress(username, progress)
                        st.success(f"Generated {len(flashcards)} flashcards (parsed fallback).")
                    else:
                        st.error("Failed to generate flashcards. Try another topic.")

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
