# ai_learning_assistant.py
import streamlit as st
import pandas as pd
import plotly.express as px
from auth import load_auth
from welcome import show_welcome_page
from ai_modules import (
    run_ai_learning_assistant,
    run_quiz,
    inject_css,
    get_quiz_results,
    update_quiz_stats,
    voice_to_notes_from_audiofile,
    get_progress_figures
)

# --- Page config must be first Streamlit command ---
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

def main():
    inject_css()  # theme/style

    # -------------------- AUTH --------------------
    authenticator = load_auth()
    # safe login
    if callable(getattr(authenticator, "login", None)):
        login_result = authenticator.login()
    else:
        login_result = authenticator

    if isinstance(login_result, tuple) and len(login_result) == 3:
        user, logged_in, username = login_result
    else:
        user, logged_in, username = (login_result if isinstance(login_result, dict) else {}, True, str(login_result))

    if not logged_in:
        st.stop()

    # -------------------- safe_user --------------------
    safe_user = {}
    if isinstance(user, dict):
        safe_user["id"] = user.get("id", 0)
        safe_user["username"] = user.get("username", username)
    else:
        safe_user["id"] = 0
        safe_user["username"] = username

    # -------------------- session state defaults --------------------
    if "page" not in st.session_state:
        st.session_state.page = "ai_study"
    if "transition" not in st.session_state:
        st.session_state.transition = "fade"
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    # -------------------- SIDEBAR NAV --------------------
    st.sidebar.title("Navigation")
    st.sidebar.write(f"👤 {safe_user['username']}")
    choice = st.sidebar.radio("Go to", ["AI Study Buddy", "Voice → Notes", "Development & Analytics", "About / Logout"])
    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    # Map choice to page
    page_map = {
        "AI Study Buddy": "ai_study",
        "Voice → Notes": "voice_notes",
        "Development & Analytics": "development",
        "About / Logout": "about"
    }
    st.session_state.page = page_map.get(choice, "ai_study")

    # -------------------- ROUTING --------------------
    if st.session_state.page == "ai_study":
        st.session_state.transition = "fade"
        run_ai_learning_assistant(safe_user)

    elif st.session_state.page == "voice_notes":
        st.session_state.transition = "slide"
        voice_to_notes_page(safe_user)

    elif st.session_state.page == "development":
        st.session_state.transition = "fade"
        development_page(safe_user["id"])

    elif st.session_state.page == "about":
        st.session_state.transition = "fade"
        show_about()

def voice_to_notes_page(safe_user):
    st.header("🎙️ Voice → Notes & Quiz")
    st.markdown("Upload a lecture audio (mp3/wav). Gemini will be used to transcribe & summarize.")
    uploaded = st.file_uploader("Upload audio (mp3/wav)", type=["mp3", "wav", "m4a"])
    if uploaded:
        with st.spinner("Transcribing and generating notes..."):
            result = voice_to_notes_from_audiofile(uploaded)
        st.markdown("### 📚 Generated Notes")
        st.write(result.get("notes", "No notes generated."))
        st.markdown("### 📋 Generated Quiz")
        quiz = result.get("quiz", [])
        if quiz:
            st.session_state.quiz_data = quiz
            st.success("Quiz created from lecture — go to 'AI Study Buddy' or take it here.")
            # Provide option to take quiz right here as well
            if st.button("Take this quiz here"):
                run_quiz(safe_user["id"])
        else:
            st.info("No quiz found in the generated output.")
        st.markdown("### 🔎 Weak Topics")
        st.write(result.get("weak_topics", []))
        # Also offer to generate tips about weak topics using text model
        if result.get("weak_topics"):
            if st.button("Generate improvement tips"):
                tips = generate_tips_for_weak_topics(result.get("weak_topics", []))
                st.write(tips)

def generate_tips_for_weak_topics(topics):
    prompt = f"Provide actionable study tips for the following weak topics: {', '.join(topics)}"
    out = generate_ai_response(prompt)
    return out

def development_page(user_id):
    st.header("📈 Development & Analytics")
    # progress over time and pie chart
    fig_time, fig_pie = get_progress_figures(user_id)
    st.markdown("### Progress Over Time (by quiz score %)")
    st.plotly_chart(fig_time, use_container_width=True)
    st.markdown("### Aggregate Performance")
    st.plotly_chart(fig_pie, use_container_width=True)

    # More analytics: live current quiz stats if any
    st.markdown("### Current Session Live Stats")
    update_quiz_stats()

    # Badges / insights
    st.markdown("### Insights")
    try:
        results = get_quiz_results(user_id)
        if results:
            avg_score = sum(r[0] for r in results) / max(1, len(results))
            st.write(f"Average raw score (per quiz): {avg_score:.2f}")
        else:
            st.info("No historical quiz data.")
    except Exception:
        st.warning("Could not fetch historical results.")

def show_about():
    st.header("About / Help")
    st.markdown(
        """
        - **AI Study Buddy**: Generate explanations, quizzes, flashcards. Take quizzes question-by-question.
        - **Voice → Notes**: Upload lecture audio; Gemini used to transcribe, summarize and produce quizzes and weak-topic insights.
        - **Development & Analytics**: Progress graphs, performance pie chart, and live stats.
        """
    )

# Entrypoint
if __name__ == "__main__":
    main()
