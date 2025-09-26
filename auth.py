import streamlit as st
from database import create_user, authenticate

def main():
    # -------------------- PAGE CONFIG --------------------
    #st.set_page_config(page_title="AI Learning Assistant | Login", layout="centered")

    # -------------------- PAGE STYLING --------------------
    page_bg_img = '''
    <style>
    .stApp {
        background-image: linear-gradient(to bottom right, #a8e063, #56ab2f);
        background-size: cover;
        background-position: center;
    }
    .login-box {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        border-radius: 20px;
        max-width: 420px;
        margin: auto;
        margin-top: 6rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
    }
    h1, h2, h3, h4 {
        color: #2e7d32 !important;
        text-align: center;
    }
    .stButton > button {
        width: 100%;
        background-color: #43a047 !important;
        color: white !important;
        border-radius: 10px;
        padding: 0.6rem;
        font-weight: 600;
        border: none;
    }
    .stButton > button:hover {
        background-color: #2e7d32 !important;
        color: #fff !important;
    }
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

    # -------------------- HEADER --------------------
    st.title("🎓 AI Learning Assistant")
    st.subheader("Empowering Students to Learn Smarter")
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])

    # -------------------- LOGIN TAB --------------------
    with tab_login:
        st.subheader("Login to Your Account")
        name = st.text_input("👤 Name", key="login_name")
        password = st.text_input("🔒 Password", type="password", key="login_password")

        if st.button("Login"):
            if name and password:
                user = authenticate(name, password)
                if user:
                    st.session_state["user_id"] = user.id
                    st.session_state["username"] = user.name
                    st.session_state["logged_in"] = True
                    st.success(f"✅ Welcome back, {user.name}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")
            else:
                st.warning("⚠️ Please enter both username and password.")

    # -------------------- SIGNUP TAB --------------------
    with tab_signup:
        st.subheader("Create a New Account")
        new_name = st.text_input("👤 Full Name", key="signup_name")
        new_email = st.text_input("📧 Gmail", key="signup_email")
        new_password = st.text_input("🔒 Password", type="password", key="signup_password")

        if st.button("Sign Up"):
            if new_name and new_email and new_password:
                user = create_user(new_name, new_email, new_password)
                if user:
                    st.success("🎉 Account created successfully! Please log in.")
                else:
                    st.error("⚠️ User with this name or email already exists.")
            else:
                st.warning("⚠️ Please fill all fields before signing up.")

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------- AUTH WRAPPER CLASS --------------------
class AuthWrapper:
    def login(self, *args, **kwargs):
        main()
        logged = st.session_state.get("logged_in", False)
        username = st.session_state.get("username", "")
        return username, logged, username


def load_auth():
    """Provides an authenticator object with a login() method."""
    return AuthWrapper()
