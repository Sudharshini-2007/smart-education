"""
pages/student.py - Student dashboard with AI Tutor.

Provides:
- Sidebar navigation between student features
- PDF upload with text extraction and FAISS indexing
- RAG-powered AI Tutor with conversational context
- Three learning modes: Teach Me, Test Me, Challenge Me
- Smart suggested questions from uploaded material
- "Explain Differently" re-explanation styles
"""

import streamlit as st

# =========================================================================
# Custom CSS for premium look
# =========================================================================

CUSTOM_CSS = """
<style>
/* ---------- Global ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ---------- Header gradient ---------- */
.hero-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
}
.hero-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
}
.hero-header p {
    margin: 0.3rem 0 0 0;
    opacity: 0.85;
    font-size: 1.05rem;
    font-family: 'Inter', sans-serif;
}

/* ---------- Material card ---------- */
.material-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
    border: 1px solid #dde1e8;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.material-card.ready {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    border-color: #a5d6a7;
}
.material-card h3 {
    margin: 0 0 0.4rem 0;
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
}
.material-card .meta {
    font-size: 0.88rem;
    color: #555;
    font-family: 'Inter', sans-serif;
}

/* ---------- Chat messages ---------- */
.chat-user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 1.3rem;
    border-radius: 14px 14px 4px 14px;
    margin: 0.6rem 0;
    font-family: 'Inter', sans-serif;
    max-width: 85%;
    margin-left: auto;
}
.chat-ai {
    background: #f8f9fb;
    border: 1px solid #e2e5ea;
    padding: 1.2rem 1.5rem;
    border-radius: 14px 14px 14px 4px;
    margin: 0.6rem 0;
    font-family: 'Inter', sans-serif;
    max-width: 90%;
    line-height: 1.6;
}

/* ---------- Mode buttons ---------- */
.mode-teach {
    background: #e8f5e9 !important;
    border: 2px solid #66bb6a !important;
    border-radius: 12px !important;
    color: #2e7d32 !important;
    font-weight: 600 !important;
}
.mode-test {
    background: #fff8e1 !important;
    border: 2px solid #ffa726 !important;
    border-radius: 12px !important;
    color: #e65100 !important;
    font-weight: 600 !important;
}
.mode-challenge {
    background: #fce4ec !important;
    border: 2px solid #ef5350 !important;
    border-radius: 12px !important;
    color: #c62828 !important;
    font-weight: 600 !important;
}

/* ---------- Suggested question chips ---------- */
.sq-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.8rem 0;
}

/* ---------- Section label ---------- */
.section-label {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: #444;
    margin: 1.2rem 0 0.5rem 0;
}

/* ---------- Nav Cards (Dashboard) ---------- */
.nav-card {
    background: #ffffff;
    border: 1px solid #e0e5ec;
    border-radius: 12px;
    padding: 1.5rem;
    height: 100%;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 0.5rem;
}
.nav-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.05);
    border-color: #667eea;
}
.nav-card h3 {
    margin: 0 0 0.5rem 0;
    font-family: 'Inter', sans-serif;
    color: #2c3e50;
    font-size: 1.2rem;
}
.nav-card p {
    margin: 0 0 1rem 0;
    color: #5c6b7a;
    font-size: 0.9rem;
    line-height: 1.4;
}

/* ---------- Journey Flow ---------- */
.journey-flow {
    text-align: center;
    padding: 1rem;
    color: #5c6b7a;
    font-size: 0.95rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
    background: #f8f9fb;
    border-radius: 10px;
    margin-bottom: 2rem;
    border: 1px dashed #d1d8e0;
}
.journey-flow span {
    color: #667eea;
    font-weight: 600;
}

/* ---------- Sidebar styling ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}
section[data-testid="stSidebar"] .stMarkdown {
    color: #e0e0e0;
}
</style>
"""


# =========================================================================
# Session state initialisation
# =========================================================================

def _init_session_state():
    """Initialise all session-state keys used by the student dashboard."""
    defaults = {
        "student_section": "learning_journey",
        # PDF state
        "pdf_name": None,
        "pdf_pages": 0,
        "pdf_chunks": [],
        # Services (created lazily)
        "ai_service": None,
        "rag_service": None,
        # Chat
        "chat_history": [],       # list of {"role": ..., "content": ...}
        # Suggested questions
        "suggested_questions": [],
        # Learning mode
        "current_mode": "ask",    # ask | teach | test | challenge
        "awaiting_test_answer": False,
        "test_question_text": None,
        # Explain differently
        "last_ai_response": None,
        "last_question": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# =========================================================================
# Lazy service factories
# =========================================================================

def _get_ai_service():
    """Return (or create) the AIService singleton in session state."""
    if st.session_state.ai_service is None:
        from services.ai_service import AIService
        st.session_state.ai_service = AIService()
    return st.session_state.ai_service


def _get_rag_service():
    """Return (or create) the RAGService singleton in session state."""
    if st.session_state.get("rag_service") is None:
        from services.rag_service import RAGService
        st.session_state.rag_service = RAGService()
    rag = st.session_state.rag_service
    if not rag.is_ready and st.session_state.get("pdf_chunks"):
        ai = _get_ai_service()
        try:
            rag.build_index(st.session_state.pdf_chunks, ai)
        except Exception:
            pass
    return rag


# =========================================================================
# AI availability check
# =========================================================================

def _check_ai_status():
    """Show a warning banner if Ollama is not reachable."""
    ai = _get_ai_service()
    if not ai.check_available():
        st.warning(
            "⚠️ **AI features are unavailable.** Ollama is not running.\n\n"
            "Start it with `ollama serve` and make sure `mistral` and "
            "`nomic-embed-text` models are pulled.",
            icon="🔌",
        )
        return False
    return True


# =========================================================================
# PDF upload & processing
# =========================================================================

def _render_pdf_upload():
    """Render the study material upload card and process uploads."""

    # --- Material status card ---
    if st.session_state.pdf_name:
        st.markdown(
            f'<div class="material-card ready">'
            f'<h3>📄 {st.session_state.pdf_name}</h3>'
            f'<div class="meta">'
            f'📃 {st.session_state.pdf_pages} page(s) · '
            f'📦 {len(st.session_state.pdf_chunks)} chunks · '
            f'✅ Ready to learn</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="material-card">'
            '<h3>📄 No Study Material Uploaded</h3>'
            '<div class="meta">Upload a PDF to unlock AI features</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Show success message if available
    if st.session_state.get("pdf_upload_msg"):
        st.success(st.session_state.pdf_upload_msg)

    # --- Uploader ---
    uploaded = st.file_uploader(
        "Upload study material (PDF)",
        type=["pdf"],
        key="pdf_uploader",
        label_visibility="collapsed",
    )

    if uploaded is not None and uploaded.name != st.session_state.pdf_name:
        _process_pdf(uploaded)


def _process_pdf(uploaded_file):
    """Extract text, chunk it, build FAISS index, and generate questions."""
    from services.pdf_service import extract_text_from_pdf, clean_text, chunk_text

    ai = _get_ai_service()
    rag = _get_rag_service()

    # Check AI before expensive operations
    if not ai.check_available():
        st.error(
            "⚠️ Cannot process PDF — Ollama is not running. "
            "Start Ollama and try again."
        )
        return

    try:
        with st.spinner("📖 Extracting text from PDF..."):
            raw_text, num_pages = extract_text_from_pdf(uploaded_file)
            cleaned = clean_text(raw_text)
            chunks = chunk_text(cleaned)

            if not chunks:
                st.error("⚠️ No usable text found in this PDF.")
                return

        with st.spinner(f"🧠 Creating embeddings for {len(chunks)} chunks..."):
            rag.build_index(chunks, ai)

        with st.spinner("💡 Generating suggested questions..."):
            questions = rag.generate_suggested_questions(ai)

        # Save to session state
        st.session_state.pdf_name = uploaded_file.name
        st.session_state.pdf_pages = num_pages
        st.session_state.pdf_chunks = chunks
        st.session_state.suggested_questions = questions
        st.session_state.pdf_upload_msg = (
            f"✅ **{uploaded_file.name}** processed successfully! "
            f"({num_pages} pages, {len(chunks)} chunks)"
        )
        # Reset chat for new material
        st.session_state.chat_history = []
        st.session_state.current_mode = "ask"
        st.session_state.awaiting_test_answer = False

        st.rerun()

    except ValueError as e:
        st.error(f"⚠️ {e}")
    except ConnectionError as e:
        st.error(f"🔌 {e}")
    except Exception as e:
        st.error(f"⚠️ Your study material couldn't be processed. Please try another PDF.\n\nDetails: {e}")


# =========================================================================
# Suggested questions
# =========================================================================

def _render_suggested_questions():
    """Display clickable suggested question buttons."""
    questions = st.session_state.suggested_questions
    if not questions:
        return

    st.markdown('<div class="section-label">💡 Suggested Questions</div>', unsafe_allow_html=True)

    cols = st.columns(min(len(questions), 3))
    for i, q in enumerate(questions):
        with cols[i % 3]:
            if st.button(f"💬 {q}", key=f"sq_{i}", use_container_width=True):
                _send_message(q)


# =========================================================================
# Learning modes
# =========================================================================

def _render_learning_modes():
    """Render the three learning mode buttons."""
    if not st.session_state.pdf_name:
        return

    st.markdown('<div class="section-label">🎯 Learning Modes</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🟢 Teach Me", key="mode_teach", use_container_width=True):
            st.session_state.current_mode = "teach"
            st.session_state.awaiting_test_answer = False
            st.toast("Mode: **Teach Me** — Ask anything and get a beginner-friendly explanation!", icon="🟢")

    with c2:
        if st.button("🟡 Test Me", key="mode_test", use_container_width=True):
            st.session_state.current_mode = "test"
            st.session_state.awaiting_test_answer = False
            st.toast("Mode: **Test Me** — I'll ask YOU a question!", icon="🟡")

    with c3:
        if st.button("🔴 Challenge Me", key="mode_challenge", use_container_width=True):
            st.session_state.current_mode = "challenge"
            st.session_state.awaiting_test_answer = False
            st.toast("Mode: **Challenge Me** — Get ready for a hard problem!", icon="🔴")

    # Show active mode indicator
    mode_labels = {
        "ask": "💬 Free Ask",
        "teach": "🟢 Teach Me",
        "test": "🟡 Test Me",
        "challenge": "🔴 Challenge Me",
    }
    st.caption(f"Active mode: **{mode_labels.get(st.session_state.current_mode, 'Ask')}**")


# =========================================================================
# Chat interface
# =========================================================================

def _render_chat():
    """Render the chat history and input."""
    st.markdown('<div class="section-label">🤖 AI Tutor</div>', unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            with st.container(border=True):
                st.markdown(msg["content"])

    # Explain Differently (shown after last AI response)
    if st.session_state.last_ai_response and st.session_state.chat_history:
        _render_explain_differently()

    # Input area
    if st.session_state.awaiting_test_answer:
        user_input = st.chat_input("Type your answer here...")
        if user_input:
            _handle_test_answer(user_input)
    else:
        placeholder_text = {
            "ask": "Ask anything about your study material...",
            "teach": "What topic should I teach you about?",
            "test": "What topic should I test you on?",
            "challenge": "What topic do you want a challenge on?",
        }
        user_input = st.chat_input(
            placeholder_text.get(st.session_state.current_mode, "Ask a question...")
        )
        if user_input:
            _send_message(user_input)


def _send_message(question: str):
    """Process a user message through the RAG pipeline."""
    ai = _get_ai_service()
    rag = _get_rag_service()

    if not ai.check_available():
        st.error("🔌 Ollama is not running. Please start it to use AI features.")
        return

    if not rag.is_ready:
        st.warning("📄 Please upload study material first.")
        return

    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": question})

    # Choose template based on current mode
    mode = st.session_state.current_mode
    template_map = {
        "ask": "rag_answer",
        "teach": "teach_me",
        "test": "test_me",
        "challenge": "challenge_me",
    }
    template_name = template_map.get(mode, "rag_answer")

    try:
        with st.spinner("🧠 Thinking..."):
            response = rag.answer_question(
                question=question,
                ai_service=ai,
                template_name=template_name,
                chat_history=st.session_state.chat_history[:-1],  # exclude current
            )

        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.session_state.last_ai_response = response
        st.session_state.last_question = question

        # If test mode, wait for student's answer
        if mode == "test":
            st.session_state.awaiting_test_answer = True
            st.session_state.test_question_text = response

        st.rerun()

    except ConnectionError as e:
        st.error(f"🔌 {e}")
    except Exception as e:
        st.error(f"⚠️ Something went wrong: {e}")


def _handle_test_answer(student_answer: str):
    """Evaluate the student's answer to a test question."""
    ai = _get_ai_service()
    rag = _get_rag_service()

    st.session_state.chat_history.append({"role": "user", "content": student_answer})

    try:
        with st.spinner("📝 Evaluating your answer..."):
            response = rag.answer_question(
                question=st.session_state.last_question or "",
                ai_service=ai,
                template_name="evaluate_answer",
                chat_history=st.session_state.chat_history[:-1],
                extra_vars={"student_answer": student_answer},
            )

        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.session_state.last_ai_response = response
        st.session_state.awaiting_test_answer = False

        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Could not evaluate your answer: {e}")


# =========================================================================
# Explain Differently
# =========================================================================

def _render_explain_differently():
    """Show re-explanation style buttons after an AI response."""
    st.markdown('<div class="section-label">🔄 Explain Differently</div>', unsafe_allow_html=True)

    styles = [
        ("🧒 Beginner", "explain_beginner"),
        ("🌍 Analogy", "explain_analogy"),
        ("📖 Academic", "explain_academic"),
        ("💻 Code Example", "explain_code"),
        ("⚡ 30s Revision", "explain_quick"),
    ]

    cols = st.columns(len(styles))
    for i, (label, template_name) in enumerate(styles):
        with cols[i]:
            if st.button(label, key=f"ed_{template_name}", use_container_width=True):
                _explain_differently(template_name)


def _explain_differently(template_name: str):
    """Re-explain the last concept in a different style."""
    ai = _get_ai_service()
    rag = _get_rag_service()

    question = st.session_state.last_question
    if not question:
        st.warning("Ask a question first!")
        return

    try:
        with st.spinner("🔄 Re-explaining..."):
            response = rag.answer_question(
                question=question,
                ai_service=ai,
                template_name=template_name,
                chat_history=st.session_state.chat_history[-4:],
            )

        st.session_state.chat_history.append(
            {"role": "assistant", "content": response}
        )
        st.session_state.last_ai_response = response
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Re-explanation failed: {e}")


# =========================================================================
# Sidebar navigation
# =========================================================================

def _render_sidebar():
    """Add student-specific navigation items to the sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("#### 📚 Student Menu")

        nav_items = [
            ("✨ Learning Journey", "learning_journey"),
            ("🤖 AI Tutor", "ai_tutor"),
            ("📝 Assessments", "assessment"),
            ("📚 Study Workflow", "study_workflow"),
            ("💻 Skill Journey", "skills"),
            ("📝 Assignments", "assignments"),
        ]

        for label, key in nav_items:
            is_active = st.session_state.student_section == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
                st.session_state.student_section = key
                st.rerun()


# =========================================================================
# Placeholder sections (for future steps)
# =========================================================================

def _render_placeholder(title: str, icon: str, description: str):
    """Render a placeholder card for unimplemented features."""
    st.markdown(
        f'<div class="hero-header" style="background: linear-gradient(135deg, #546e7a 0%, #37474f 100%);">'
        f'<h1>{icon} {title}</h1>'
        f'<p>{description}</p></div>',
        unsafe_allow_html=True,
    )
    st.info("🔜 This feature will be implemented in a future step.")


# =========================================================================
# Main entry point
# =========================================================================

def show():
    """Render the Student Dashboard."""
    _init_session_state()

    # Inject custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Sidebar navigation
    _render_sidebar()

    # Route to the selected section
    section = st.session_state.student_section

    if section == "learning_journey":
        _show_learning_journey()
    elif section == "ai_tutor":
        _show_ai_tutor()
    elif section == "study_workflow":
        from pages import study_workflow
        study_workflow.show()
    elif section == "assessment":
        from pages import assessment
        assessment.show()
    elif section == "skills":
        from pages import skill_journey
        skill_journey.show()
    elif section == "assignments":
        _show_assignments()
    else:
        _show_learning_journey()

def _show_learning_journey():
    """Render the Student Dashboard Overview with attractive cards."""
    # Header
    st.markdown(
        '<div class="hero-header">'
        '<h1>✨ Your Learning Journey</h1>'
        '<p>Learn · Practice · Identify Gaps · Improve</p></div>',
        unsafe_allow_html=True,
    )

    # Unique visual element connection
    st.markdown(
        '<div class="journey-flow">'
        '<span>Student Performance</span> &nbsp;→&nbsp; '
        '<span>Learning Gap</span> &nbsp;→&nbsp; '
        '<span>AI Insight</span> &nbsp;→&nbsp; '
        '<span>Recommended Action</span> &nbsp;→&nbsp; '
        '<span>Improvement</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 🗺️ Explore your space")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(
            '<div class="nav-card">'
            '<h3>🤖 AI Tutor</h3>'
            '<p>Your personal AI guide. Ask questions and master new concepts dynamically.</p>'
            '</div>', unsafe_allow_html=True
        )
        if st.button("Enter AI Tutor", use_container_width=True):
            st.session_state.student_section = "ai_tutor"
            st.rerun()

    with c2:
        st.markdown(
            '<div class="nav-card">'
            '<h3>📝 Assessments</h3>'
            '<p>Test your knowledge, identify weak spots, and practice adaptively.</p>'
            '</div>', unsafe_allow_html=True
        )
        if st.button("Take Assessment", use_container_width=True):
            st.session_state.student_section = "assessment"
            st.rerun()

    with c3:
        st.markdown(
            '<div class="nav-card">'
            '<h3>📚 Study Workflow</h3>'
            '<p>Generate structured study plans and track your long-term goals.</p>'
            '</div>', unsafe_allow_html=True
        )
        if st.button("View Study Plans", use_container_width=True):
            st.session_state.student_section = "study_workflow"
            st.rerun()

    c4, c5, c6 = st.columns(3)
    
    with c4:
        st.markdown(
            '<div class="nav-card">'
            '<h3>💻 Skill Journey</h3>'
            '<p>Master specific skills through a gamified, node-based progression tree.</p>'
            '</div>', unsafe_allow_html=True
        )
        if st.button("Develop Skills", use_container_width=True):
            st.session_state.student_section = "skills"
            st.rerun()

    with c5:
        st.markdown(
            '<div class="nav-card">'
            '<h3>📝 Assignments</h3>'
            '<p>Complete targeted tasks and quizzes assigned by your teacher.</p>'
            '</div>', unsafe_allow_html=True
        )
        if st.button("View Assignments", use_container_width=True):
            st.session_state.student_section = "assignments"
            st.rerun()


def _show_ai_tutor():
    """Render the full AI Tutor section."""

    # Header
    st.markdown(
        '<div class="hero-header">'
        '<h1>✨ Your Learning Space</h1>'
        '<p>Learn · Practice · Master</p></div>',
        unsafe_allow_html=True,
    )

    # Check AI status
    ai_ok = _check_ai_status()

    # Study Material upload
    _render_pdf_upload()

    # Only show AI features if material is uploaded
    if st.session_state.pdf_name:
        # Suggested questions
        _render_suggested_questions()

        # Learning modes
        _render_learning_modes()

        # Chat
        _render_chat()

    elif ai_ok:
        st.markdown("---")
        st.markdown(
            "### 👆 Upload a PDF to get started\n\n"
            "Once you upload your study material, you'll be able to:\n"
            "- 💬 Ask questions about the content\n"
            "- 🟢 Get beginner-friendly explanations\n"
            "- 🟡 Test your understanding\n"
            "- 🔴 Challenge yourself with hard problems"
        )


# =========================================================================
# Assignments Section
# =========================================================================

def _get_current_student_id():
    from services.classroom_service import get_students, add_student
    students = get_students()
    if students:
        return students[0]["id"]
    return add_student("Current Student", "student@example.com")


def _show_assignments():
    """Render the Student Assignments section."""
    from services.classroom_service import get_assignments, get_assignment_submissions, submit_assignment

    st.markdown(
        '<div class="hero-header" style="background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);">'
        '<h1>📝 Your Assignments</h1>'
        '<p>Complete your tasks and submit your work below.</p></div>',
        unsafe_allow_html=True,
    )

    student_id = _get_current_student_id()
    if not student_id:
        st.warning("⚠️ Could not load student profile.")
        return

    assignments = get_assignments()
    if not assignments:
        st.info("🎉 No assignments yet.")
        return

    # View assignment state
    if "view_assignment_id" not in st.session_state:
        st.session_state.view_assignment_id = None

    if st.session_state.view_assignment_id:
        a_id = st.session_state.view_assignment_id
        assignment = next((a for a in assignments if a["id"] == a_id), None)
        
        if not assignment:
            st.session_state.view_assignment_id = None
            st.rerun()

        st.button("⬅️ Back to Assignments", on_click=lambda: st.session_state.update({"view_assignment_id": None}))
        st.markdown(f"### {assignment['title']}")
        st.caption(f"**Topic:** {assignment['topic']} | **Deadline:** {assignment['deadline']}")
        st.info(assignment['description'])

        subs = get_assignment_submissions(a_id)
        my_sub = next((s for s in subs if s["student_id"] == student_id), None)

        if my_sub:
            st.success("✅ Submitted")
            st.markdown("#### Your Submission")
            st.text_area("Content", value=my_sub["content"], disabled=True, height=150)
        else:
            st.markdown("#### Submit Your Work")
            with st.form(f"submit_form_{a_id}"):
                content = st.text_area("Your Submission", height=150, placeholder="Type your answer or paste your link here...")
                submitted = st.form_submit_button("Submit Assignment", type="primary", use_container_width=True)
                if submitted:
                    if not content.strip():
                        st.error("Submission cannot be empty.")
                    else:
                        submit_assignment(a_id, student_id, content)
                        st.success("✅ Assignment submitted successfully!")
                        st.session_state.view_assignment_id = None
                        st.rerun()
        return

    # List assignments
    for a in assignments:
        subs = get_assignment_submissions(a["id"])
        is_submitted = any(s["student_id"] == student_id for s in subs)
        status_text = "✅ Submitted" if is_submitted else "⏳ Pending"
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"#### {a['title']}")
                st.caption(f"**Topic:** {a['topic']} • **Deadline:** {a['deadline']}")
                st.write(a["description"][:150] + "..." if len(a["description"]) > 150 else a["description"])
            with col2:
                st.markdown(f"**Status:** {status_text}")
                if not is_submitted:
                    if st.button("View Assignment", key=f"view_{a['id']}", use_container_width=True):
                        st.session_state.view_assignment_id = a["id"]
                        st.rerun()
                else:
                    if st.button("View Submission", key=f"view_sub_{a['id']}", use_container_width=True):
                        st.session_state.view_assignment_id = a["id"]
                        st.rerun()
