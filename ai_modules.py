import streamlit as st
import requests, tempfile, os, time
from streamlit_extras.let_it_rain import rain

API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"
MODEL = "gemini-2.0-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# -------------------- GEMINI API --------------------
def gemini_api(prompt: str):
    headers = {"Content-Type":"application/json"}
    data = {"contents":[{"parts":[{"text":prompt}]}]}
    try:
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ API Error: {e}"

# -------------------- AI QUIZ --------------------
def generate_quiz_from_text(topic):
    quiz_text = gemini_api(f"Create 5 multiple choice questions (with 4 options) on {topic}. Include correct answer.")
    try:
        import json
        quiz = json.loads(quiz_text)
        return quiz if isinstance(quiz,list) else [quiz]
    except Exception:
        return [{"question":"Sample?","options":["A","B","C","D"],"answer":"A"}]

def update_quiz_stats(progress, answers, quiz_data):
    total_correct = sum(1 for i,q in enumerate(quiz_data) if str(answers.get(i,"")).strip().lower() == str(q["answer"]).strip().lower())
    total_incorrect = len(answers) - total_correct
    weak_topics = [q.get("topic","General") for i,q in enumerate(quiz_data) if str(answers.get(i,"")).strip().lower() != str(q["answer"]).strip().lower()]
    return total_correct, total_incorrect, weak_topics

# -------------------- RUN AI QUIZ --------------------
def run_ai_quiz(progress):
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
        st.session_state.quiz_answers = {}

    topic = st.text_input("Quiz Topic (for generation):")
    if st.button("Generate Quiz") and topic.strip():
        st.session_state.quiz_data = generate_quiz_from_text(topic)
        st.session_state.quiz_answers = {}

    quiz_data = st.session_state.quiz_data
    if quiz_data:
        for i,q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q.get('question','')}**")
            options = q.get("options", ["A","B","C","D"])
            ans = st.radio(f"Select answer Q{i+1}", options, key=f"q{i}")
            st.session_state.quiz_answers[i] = ans
            st.markdown("---")
        if st.button("Submit Quiz"):
            correct, incorrect, weak = update_quiz_stats(progress, st.session_state.quiz_answers, quiz_data)
            st.success(f"✅ Correct: {correct}, ❌ Incorrect: {incorrect}")
            if weak: st.info(f"Weak Topics: {', '.join(set(weak))}")
            if correct/len(quiz_data) >= 0.8: rain(emoji="🎉", font_size=30, falling_speed=5, animation_length=2)

# -------------------- VOICE QUIZ --------------------
def run_voice_quiz(progress, live=False, uploaded_file=None):
    import speech_recognition as sr
    r = sr.Recognizer()

    if live:
        st.info("Click 'Start Recording' to speak."
                " After speaking click 'Stop' to process.")
        if st.button("Start Recording"):
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=5, phrase_time_limit=60)
                st.session_state.voice_audio = audio
        if "voice_audio" in st.session_state:
            try:
                transcription = r.recognize_google(st.session_state.voice_audio)
                st.text_area("Transcription (Live)", transcription, height=150)
                if st.button("Generate Quiz from Speech"):
                    st.session_state.quiz_data = generate_quiz_from_text(transcription)
                    st.session_state.quiz_answers = {}
                    st.success("Quiz generated from spoken content.")
            except Exception as e:
                st.error(f"Error: {e}")

    elif uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(uploaded_file.read())
            temp_path = temp.name
        st.info("Transcribing uploaded audio...")
        transcription = gemini_api(f"Transcribe and summarize lecture audio at {temp_path}")
        st.text_area("Transcription (File)", transcription, height=150)
        if st.button("Generate Quiz from File Audio"):
            st.session_state.quiz_data = generate_quiz_from_text(transcription)
            st.session_state.quiz_answers = {}
            st.success("Quiz generated from uploaded lecture audio.")
        os.remove(temp_path)
