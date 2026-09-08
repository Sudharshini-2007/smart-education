"""
app.py - Main entry point for the Smart Education platform.

Run with:
    streamlit run app.py
"""

import streamlit as st
from database import init_db

# ---------------------------------------------------------------------------
# Page configuration (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart Education",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stButton>button {
    border-radius: 8px !important;
    font-weight: 500 !important;
}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Initialise the database (creates tables on first run)
# ---------------------------------------------------------------------------
try:
    init_db()
except Exception as e:
    st.error(f"⚠️ Database initialisation failed: {e}")

# ---------------------------------------------------------------------------
# Session state — tracks which role (page) the user selected
# ---------------------------------------------------------------------------
if "role" not in st.session_state:
    st.session_state.role = None


def go_home():
    """Reset role so the user returns to the landing page."""
    st.session_state.role = None


# ---------------------------------------------------------------------------
# Sidebar (visible once a role is chosen)
# ---------------------------------------------------------------------------
if st.session_state.role:
    with st.sidebar:
        st.markdown(f"### 🎓 Smart Education")
        st.caption(f"Role: **{st.session_state.role.title()}**")
        st.divider()
        if st.button("🏠 Home", use_container_width=True):
            go_home()
            st.rerun()

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
if st.session_state.role is None:
    # ---- Landing page ----
    st.markdown(
        "<h1 style='text-align:center;'>🎓 Smart Education</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-size:1.2rem;'>"
        "AI-powered learning and classroom support platform</p>",
        unsafe_allow_html=True,
    )

    st.write("")  # spacer

    col_left, col_mid, col_right = st.columns([1, 2, 1])

    with col_mid:
        st.markdown("#### Choose your role to continue:")
        st.write("")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("👨‍🎓  Student", use_container_width=True):
                st.session_state.role = "student"
                st.rerun()
        with c2:
            if st.button("👩‍🏫  Teacher", use_container_width=True):
                st.session_state.role = "teacher"
                st.rerun()

elif st.session_state.role == "student":
    from pages import student
    student.show()

elif st.session_state.role == "teacher":
    from pages import teacher
    teacher.show()
