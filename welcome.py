import streamlit as st
from database import get_badges

def show_welcome_page(username: str):
    # -------------------- PAGE STYLE --------------------
    st.markdown("""
    <style>
    @keyframes fadeIn { from {opacity: 0; transform: translateY(30px);} to {opacity: 1; transform: translateY(0);} }
    @keyframes slideInRight { from {opacity: 0; transform: translateX(80px);} to {opacity: 1; transform: translateX(0);} }
    .stApp {
        background-image: linear-gradient(to bottom right, #a8e063, #56ab2f);
        background-size: cover;
        background-position: center;
        color: #2e7d32;
        animation: fadeIn 1s ease-out;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .welcome-box {
        background-color: rgba(255,255,255,0.92);
        padding: 3rem;
        border-radius: 25px;
        max-width: 700px;
        margin: auto;
        margin-top: 6rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        animation: fadeIn 1.2s ease-out;
    }
    h1,h2,h3 { color:#2e7d32 !important; text-align:center; }
    .tagline { font-size:1.3rem; color:#33691e; margin:1rem 0 2rem 0; font-style:italic; }
    .stButton>button {
        background: linear-gradient(90deg,#43a047,#66bb6a);
        color:white;
        font-size:1.1rem;
        border-radius:12px;
        padding:0.7rem 2rem;
        font-weight:600;
        border:none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(67,160,71,0.4);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg,#2e7d32,#43a047);
        transform: scale(1.03);
        box-shadow: 0 6px 16px rgba(46,125,50,0.6);
    }
    img { animation: fadeIn 1.4s ease-out; }
    .badge { display:inline-block; padding:0.4rem 0.8rem; margin:0.2rem; border-radius:12px; background: linear-gradient(135deg,#ffd700,#ffecb3); color:#4a4a4a; font-weight:700; box-shadow:0 4px 12px rgba(0,0,0,0.25); transition: transform 0.3s ease; }
    .badge:hover { transform: scale(1.2) rotate(-3deg); box-shadow:0 6px 20px rgba(0,0,0,0.35); }
    </style>
    """, unsafe_allow_html=True)

    # -------------------- WELCOME BOX --------------------
    with st.container():
        st.markdown("<div class='welcome-box'>", unsafe_allow_html=True)
        st.markdown(f"<h1>👋 Welcome, {username}!</h1>", unsafe_allow_html=True)
        st.markdown("<h2>AI Learning Assistant</h2>", unsafe_allow_html=True)
        st.markdown("<div class='tagline'>“Let’s take a step towards smarter learning.”</div>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3022/3022826.png", width=120)
        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------- BADGES DISPLAY --------------------
        badges = get_badges(st.session_state.get("user_id",0))
        if badges:
            st.markdown("### 🏅 Your Badges")
            for b, ts in badges:
                st.markdown(f"<span class='badge'>{b}</span>", unsafe_allow_html=True)
        else:
            st.info("No badges yet. Start interacting to earn badges!")

        # -------------------- START BUTTON --------------------
        if st.button("🚀 Let's Get Started"):
            st.session_state["page"] = "main_app"
            st.session_state["transition"] = "slide"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
