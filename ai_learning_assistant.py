import streamlit as st
from auth import load_auth
from welcome import show_welcome_page
from ai_modules import run_ai_learning_assistant  # Your AI logic

# ----------------------------- MAIN FUNCTION -----------------------------
def main():
    st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖", layout="wide")

    # -------------------- AUTHENTICATION --------------------
    authenticator = load_auth()
    user, logged_in, username = authenticator.login()

    if not logged_in:
        st.stop()

    user_id = user["id"]

    # Sidebar: user info + logout
    st.sidebar.success(f"👤 Logged in as {username}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.rerun()

    # -------------------- SESSION STATE --------------------
    if "page" not in st.session_state:
        st.session_state.page = "welcome"
    if "transition" not in st.session_state:
        st.session_state.transition = "fade"

    # -------------------- QUERY PARAMS SUPPORT --------------------
    query_params = st.query_params
    if "page" in query_params:
        page = query_params["page"][0]
        st.session_state.page = page

    # -------------------- DYNAMIC TRANSITION CSS --------------------
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
    .window-box {{
        background-color: rgba(255,255,255,0.95);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 28px rgba(0,0,0,0.25);
        animation: {st.session_state.transition} 0.8s ease-out;
        margin-bottom: 2rem;
    }}
    </style>
    """
    st.markdown(transition_css, unsafe_allow_html=True)

    # -------------------- PAGE ROUTING --------------------
    if st.session_state.page == "welcome":
        st.session_state.transition = "fade"
        with st.container():
            st.markdown("<div class='window-box'>", unsafe_allow_html=True)
            show_welcome_page(username)
            st.markdown("</div>", unsafe_allow_html=True)
    elif st.session_state.page == "main_app":
        st.session_state.transition = "slide"
        with st.container():
            st.markdown("<div class='window-box'>", unsafe_allow_html=True)
            run_ai_learning_assistant(username, user_id)
            st.markdown("</div>", unsafe_allow_html=True)
    elif st.session_state.page == "quiz":
        st.session_state.transition = "fade"
        from ai_modules import run_quiz
        with st.container():
            st.markdown("<div class='window-box'>", unsafe_allow_html=True)
            run_quiz(user_id)
            st.markdown("</div>", unsafe_allow_html=True)
    elif st.session_state.page == "development":
        st.session_state.transition = "fade"
        from ai_modules import show_progress
        with st.container():
            st.markdown("<div class='window-box'>", unsafe_allow_html=True)
            show_progress(user_id)
            st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------- ENTRY POINT -----------------------------
if __name__ == "__main__":
    main()
