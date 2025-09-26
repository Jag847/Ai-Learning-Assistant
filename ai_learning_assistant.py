import streamlit as st
from auth import load_auth
from welcome import show_welcome_page
from ai_modules import run_ai_learning_assistant 

# ----------------------------- CONFIGURATION -----------------------------
def main():
    authenticator = load_auth()
    user, logged_in, username = authenticator.login()

    if not logged_in:
        st.stop()

    # Sidebar for user info and logout
    st.sidebar.success(f"👤 Logged in as {username}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.rerun()

    # Navigation logic
    if "page" not in st.session_state:
        st.session_state["page"] = "welcome"

    if st.session_state["page"] == "welcome":
        show_welcome_page(username)
    elif st.session_state["page"] == "main_app":
        run_ai_learning_assistant(username)

if __name__ == "__main__":
    main()

