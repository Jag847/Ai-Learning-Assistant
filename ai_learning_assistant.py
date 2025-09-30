import streamlit as st
import pandas as pd
import plotly.express as px
from auth import load_auth
from welcome import show_welcome_page
from ai_modules import run_ai_learning_assistant, run_quiz, inject_css, get_quiz_results, update_quiz_stats

# ----------------------------- MAIN CONFIG -----------------------------
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

def main():
    # -------------------- CSS --------------------
    inject_css()

    # -------------------- AUTHENTICATION --------------------
    authenticator = load_auth()
    if callable(getattr(authenticator, "login", None)):
        user, logged_in, username = authenticator.login()
    else:
        user, logged_in, username = {}, True, str(authenticator)

    if not logged_in:
        st.stop()

    # -------------------- SESSION STATE --------------------
    if "page" not in st.session_state:
        st.session_state.page = "welcome"
    if "transition" not in st.session_state:
        st.session_state.transition = "fade"
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    # -------------------- SAFE USER --------------------
    safe_user = {}
    if isinstance(user, dict):
        safe_user["id"] = user.get("id", 0)
        safe_user["username"] = user.get("username", "User")
    else:
        safe_user["id"] = 0
        safe_user["username"] = username

    st.sidebar.success(f"👤 Logged in as {safe_user['username']}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    # -------------------- PAGE TRANSITIONS --------------------
    transition_css = f"""
    <style>
    @keyframes fade {{
        from {{opacity: 0;}}
        to {{opacity: 1;}}
    }}
    @keyframes slide {{
        from {{opacity: 0; transform: translateX(80px);}}
        to {{opacity: 1; transform: translateX(0);}}
    }}
    .stApp {{
        animation: {st.session_state.transition} 0.8s ease-out;
    }}
    </style>
    """
    st.markdown(transition_css, unsafe_allow_html=True)

    # -------------------- PAGE ROUTING --------------------
    if st.session_state.page == "welcome":
        st.session_state.transition = "fade"
        show_welcome_page(safe_user["username"])
    elif st.session_state.page == "main_app":
        st.session_state.transition = "slide"
        run_ai_learning_assistant(safe_user)
    elif st.session_state.page == "quiz":
        st.session_state.transition = "fade"
        run_quiz(safe_user["id"])
    elif st.session_state.page == "development":
        st.session_state.transition = "fade"
        show_development_page(safe_user["id"])

# ----------------------------- DEVELOPMENT PAGE -----------------------------
def show_development_page(user_id):
    st.subheader("📊 Your Development Dashboard")
    results = get_quiz_results(user_id)
    if not results:
        st.info("No quiz taken yet. Take a quiz to see progress.")
        return

    df = pd.DataFrame(results, columns=["score", "total", "timestamp"])
    df["percentage"] = df["score"] / df["total"] * 100

    st.markdown("### Progress Over Time")
    fig = px.line(df, x="timestamp", y="percentage", title="Quiz Scores Over Time", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Live Stats")
    update_quiz_stats()

# ----------------------------- ENTRY POINT -----------------------------
if __name__ == "__main__":
    main()
