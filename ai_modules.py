import streamlit as st
import requests

API_KEY = "AIzaSyAjwX-7ymrT5RBObzDkd2nhCFflfXEA2ts"  # your raw key
MODEL = "gemini-2.0-flash"
URL =f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

headers = {"Content-Type": "application/json"}

payload = {
    "prompt": {"text": "Explain Newton's Laws in simple terms."},
    "temperature": 0.7,
    "maxOutputTokens": 300
}

response = requests.post(URL, headers=headers, json=payload)

if response.status_code == 200:
    print(response.json())
else:
    print("Error:", response.status_code, response.text)
def generate_ai_response(prompt):
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300
        }
    } 

    try:
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"][0]["text"]
    except Exception as e:
        return f"⚠️ Error: {e}"

def run_ai_learning_assistant(username):
    st.title(f"🎓 Welcome {username}, Your AI Learning Assistant is Ready!")
    st.sidebar.header("📚 Navigation")
    menu = st.sidebar.radio("Choose a tool", ["AI Study Buddy", "Lecture Voice-to-Notes"])

    if menu == "AI Study Buddy":
        st.subheader("🧩 AI Study Buddy — Understand & Revise Smarter")
        text = st.text_area("Enter topic or material:", height=200)
        task = st.selectbox("Choose an action:", ["Explain in simple terms", "Summarize", "Generate quiz", "Create flashcards"])
        if st.button("✨ Generate"):
            if text.strip():
                with st.spinner("AI is working..."):
                    result = generate_ai_response(f"{task} this content:\n{text}")
                st.success("✅ Result:")
                st.write(result)
            else:
                st.warning("Please enter some text.")

    elif menu == "Lecture Voice-to-Notes":
        st.subheader("🎤 Lecture Voice-to-Notes Generator")
        file = st.file_uploader("Upload Lecture Audio (mp3/wav)", type=["mp3", "wav"])
        if file:
            st.audio(file)
            st.info("Simulating transcription... (Replace with Whisper/Speech API)")
            transcription = "Photosynthesis is the process by which green plants convert light energy..."
            st.write("🗒️ Transcribed Text:")
            st.write(transcription)

            action = st.selectbox("Generate:", ["Summary", "Quiz", "Flashcards"])
            if st.button("🚀 Generate Notes"):
                with st.spinner("Generating..."):
                    result = generate_ai_response(f"{action} based on: {transcription}")
                st.success("✅ Generated:")
                st.write(result)
