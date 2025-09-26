import streamlit as st

def show_welcome_page(username: str):
    #st.set_page_config(page_title="Welcome | AI Learning Assistant", layout="centered")

    # -------------------- PAGE STYLE --------------------
    page_bg = """
    <style>
    .stApp {
        background-image: linear-gradient(to bottom right, #a8e063, #56ab2f);
        background-size: cover;
        background-position: center;
        color: #2e7d32;
    }
    .welcome-box {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 3rem;
        border-radius: 25px;
        max-width: 700px;
        margin: auto;
        margin-top: 6rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }
    h1, h2, h3 {
        color: #2e7d32 !important;
        text-align: center;
        font-family: 'Trebuchet MS', sans-serif;
    }
    .tagline {
        font-size: 1.3rem;
        color: #33691e;
        margin-top: 1rem;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .stButton > button {
        background-color: #43a047 !important;
        color: white !important;
        font-size: 1.1rem;
        border-radius: 12px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        border: none;
    }
    .stButton > button:hover {
        background-color: #2e7d32 !important;
    }
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

    # -------------------- WELCOME BOX --------------------
    with st.container():
        st.markdown("<div class='welcome-box'>", unsafe_allow_html=True)
        st.markdown(f"<h1>👋 Welcome, {username}!</h1>", unsafe_allow_html=True)
        st.markdown("<h2>AI Learning Assistant</h2>", unsafe_allow_html=True)
        st.markdown("<div class='tagline'>“Let’s take a step towards smarter learning.”</div>", unsafe_allow_html=True)

        st.image("https://cdn-icons-png.flaticon.com/512/3022/3022826.png", width=120)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Let's Get Started"):
            st.session_state["page"] = "main_app"  # Navigate to the main assistant page
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
