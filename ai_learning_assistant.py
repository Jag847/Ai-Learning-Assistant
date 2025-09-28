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
    update_quiz_stats
)

# ----------------------------- PAGE CONFIG -----------------------------
st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

# ----------------------------- MAIN FUNCTION -----------------------------
def main():
    # -------------------- CSS --------------------
    inject_css()  # inject modern styles

    # -------------------- AUTHENTICATION --------------------
    authenticator = load_auth()

    # Safe login handling
    if callable(getattr(authenticator, "login", None)):
        result = authenticator.login()
        if isinstance(result, tuple) and len(result) == 3:
            user, logged_in, username = result
        else:
            user = result
            logged_in = True
            username = str(result)
    else:
        user = authenticator
        logged_in = True
        username = str(authenticator)

    if not logged_in:
        st.stop()

    st.sidebar.success(f"👤 Logged in as {username}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    # -------------------- SESSION STATE --------------------
    if "page" not in st.session_state:
        st.session_state.page = "welcome"
    if "transition" not in st.session_state:
        st.session_state.transition = "fade"

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

    # -------------------- SAFE USER ID --------------------
    user_id = 0
    if isinstance(user, dict):
        user_id = user.get("id", 0)

    # -------------------- PAGE ROUTING --------------------
    if st.session_state.page == "welcome":
        st.session_state.transition = "fade"
        show_welcome_page(username)
    elif st.session_state.page == "main_app":
        st.session_state.transition = "slide"
        run_ai_learning_assistant(username, user_id)
    elif st.session_state.page == "quiz":
        st.session_state.transition = "fade"
        run_quiz(user_id)
    elif st.session_state.page == "development":
        st.session_state.transition = "fade"
        show_development_page(user_id)

# ----------------------------- DEVELOPMENT PAGE -----------------------------
def show_development_page(user_id):
    st.subheader("📊 Your Development Dashboard")
    results = get_quiz_results(user_id)
    if not results:
        st.info("No quiz taken yet. Take a quiz to see progress.")
        return

    # Safe DataFrame creation
    try:
        df = pd.DataFrame(results)
        if not {"score", "total", "timestamp"}.issubset(df.columns):
            df.columns = ["score", "total", "timestamp"]
    except Exception:
        st.error("Error processing quiz results.")
        return

    df["percentage"] = df["score"] / df["total"] * 100

    st.markdown("### Progress Over Time")
    try:
        fig = px.line(df, x="timestamp", y="percentage", title="Quiz Scores Over Time", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.error("Error generating progress chart.")

    st.markdown("### Live Stats")
    try:
        update_quiz_stats()
    except Exception:
        st.warning("Unable to update live stats at this moment.")

# ----------------------------- ENTRY POINT -----------------------------
if __name__ == "__main__":
    main()
