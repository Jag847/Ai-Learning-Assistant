import streamlit as st
from auth import load_auth
from welcome import show_welcome_page
from ai_modules import run_ai_learning_assistant,run_quiz, inject_css

# ----------------------------- MAIN FUNCTION -----------------------------
def main():
    st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

    # -------------------- CSS --------------------
    inject_css()  # inject modern styles

    # -------------------- AUTHENTICATION --------------------
    authenticator = load_auth()
    user, logged_in, username = authenticator.login()
    if not logged_in:
        st.stop()

    st.sidebar.success(f"👤 Logged in as {username}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.rerun()

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

    # -------------------- PAGE ROUTING --------------------
    if st.session_state.page == "welcome":
        st.session_state.transition = "fade"
        show_welcome_page(username)
    elif st.session_state.page == "main_app":
        st.session_state.transition = "slide"
        run_ai_learning_assistant(username, user['id'])
    elif st.session_state.page == "quiz":
        st.session_state.transition = "fade"
        run_quiz(user['id'])
    elif st.session_state.page == "development":
        st.session_state.transition = "fade"
        show_development_page(user['id'])

# ----------------------------- DEVELOPMENT PAGE -----------------------------
def show_development_page(user_id):
    from ai_modules import get_quiz_results, update_quiz_stats
    st.subheader("📊 Your Development Dashboard")
    results = get_quiz_results(user_id)
    if not results:
        st.info("No quiz taken yet. Take a quiz to see progress.")
        return

    df = pd.DataFrame(results, columns=["score","total","timestamp"])
    df["percentage"] = df["score"]/df["total"]*100

    st.markdown("### Progress Over Time")
    fig = px.line(df, x="timestamp", y="percentage", title="Quiz Scores Over Time", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Live Stats")
    update_quiz_stats()

# ----------------------------- ENTRY POINT -----------------------------
if __name__ == "__main__":
    main()
