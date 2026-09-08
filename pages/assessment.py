"""
pages/assessment.py - AI Assessment & Adaptive Practice.

Provides:
- Quiz setup (topic, count, difficulty)
- Question-by-question quiz interface with progress bar
- Deterministic scoring and result dashboard
- Weak topic detection with visual analysis
- AI explanations for wrong answers
- Adaptive practice: learn → practice → retest with improvement tracking
- Integration with AI Tutor for weak topics
"""

import streamlit as st

# =========================================================================
# Custom CSS (extends the student dashboard styles)
# =========================================================================

ASSESSMENT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ---------- Score circle ---------- */
.score-circle {
    text-align: center;
    padding: 2rem;
}
.score-circle .percentage {
    font-size: 3.5rem;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.score-circle .fraction {
    font-size: 1.3rem;
    color: #666;
    font-family: 'Inter', sans-serif;
}

/* ---------- Topic cards ---------- */
.topic-strong {
    background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
    border-left: 4px solid #43a047;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin: 0.4rem 0;
    font-family: 'Inter', sans-serif;
}
.topic-attention {
    background: linear-gradient(135deg, #fff8e1, #ffecb3);
    border-left: 4px solid #ffa726;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin: 0.4rem 0;
    font-family: 'Inter', sans-serif;
}
.topic-weak {
    background: linear-gradient(135deg, #fce4ec, #f8bbd0);
    border-left: 4px solid #ef5350;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin: 0.4rem 0;
    font-family: 'Inter', sans-serif;
}

/* ---------- Question card ---------- */
.question-card {
    background: #fafbfd;
    border: 1px solid #e0e3e8;
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin: 1rem 0;
    font-family: 'Inter', sans-serif;
}
.question-card h3 {
    margin: 0 0 1rem 0;
    color: #333;
}

/* ---------- Review cards ---------- */
.review-correct {
    background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
    border: 1px solid #a5d6a7;
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.8rem 0;
}
.review-wrong {
    background: linear-gradient(135deg, #fce4ec, #fff3e0);
    border: 1px solid #ef9a9a;
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.8rem 0;
}

/* ---------- Improvement badge ---------- */
.improvement-badge {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 0.5rem 1.2rem;
    border-radius: 20px;
    font-weight: 600;
    display: inline-block;
    font-family: 'Inter', sans-serif;
}
</style>
"""


# =========================================================================
# Session state
# =========================================================================

def _init_assessment_state():
    """Initialise assessment-specific session state."""
    defaults = {
        "quiz_phase": "setup",       # setup | quiz | result | review | practice
        "quiz_questions": [],        # list of question dicts
        "quiz_answers": {},          # {index: "A"/"B"/"C"/"D"}
        "quiz_current_q": 0,         # current question index
        "quiz_result": None,         # score_quiz output
        "quiz_topic": "General",
        "quiz_difficulty": "Medium",
        "quiz_num_questions": 5,
        "quiz_weak_topics": None,    # detect_weak_topics output
        "quiz_explanations": {},     # {index: explanation_str}
        # Adaptive practice
        "practice_topic": None,
        "practice_lesson": None,
        "practice_questions": [],
        "practice_answers": {},
        "practice_result": None,
        "practice_previous_pct": None,
        # Retest
        "retest_mode": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _reset_quiz():
    """Reset quiz state for a fresh start."""
    st.session_state.quiz_phase = "setup"
    st.session_state.quiz_questions = []
    st.session_state.quiz_answers = {}
    st.session_state.quiz_current_q = 0
    st.session_state.quiz_result = None
    st.session_state.quiz_weak_topics = None
    st.session_state.quiz_explanations = {}
    st.session_state.practice_topic = None
    st.session_state.practice_lesson = None
    st.session_state.practice_questions = []
    st.session_state.practice_answers = {}
    st.session_state.practice_result = None
    st.session_state.practice_previous_pct = None
    st.session_state.retest_mode = False


# =========================================================================
# Helper to get services from student.py's session state
# =========================================================================

def _get_ai():
    if st.session_state.get("ai_service") is None:
        from services.ai_service import AIService
        st.session_state.ai_service = AIService()
    return st.session_state.ai_service


def _get_rag():
    if st.session_state.get("rag_service") is None:
        from services.rag_service import RAGService
        st.session_state.rag_service = RAGService()
    return st.session_state.rag_service


# =========================================================================
# PHASE: Setup
# =========================================================================

def _render_setup():
    """Render quiz setup form."""

    # Check prerequisites
    if not st.session_state.get("pdf_name"):
        st.info(
            "📄 **Upload study material first.**\n\n"
            "Go to 🧠 AI Tutor and upload a PDF, then come back here to take a quiz."
        )
        return

    ai = _get_ai()
    if not ai.check_available():
        st.warning(
            "⚠️ **AI is unavailable.** Ollama is not running.\n\n"
            "Start it with `ollama serve` to generate quizzes.",
            icon="🔌",
        )
        return

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### ⚡ Quick Quiz")
            st.caption("5 questions, medium difficulty, from your material")
            if st.button("Generate Quick Quiz", key="quick_quiz", use_container_width=True, type="primary"):
                _start_quiz("General", 5, "Medium")

    with col2:
        with st.container(border=True):
            st.markdown("#### 📋 Custom Practice Test")
            st.caption("Choose topic, count, and difficulty")

            topic = st.text_input(
                "Topic (or leave as General)",
                value="General",
                key="setup_topic",
            )
            num_q = st.radio(
                "Number of questions",
                options=[5, 10],
                horizontal=True,
                key="setup_num_q",
            )
            diff = st.radio(
                "Difficulty",
                options=["Easy", "Medium", "Hard"],
                horizontal=True,
                key="setup_diff",
            )

            if st.button("Generate Practice Test", key="practice_test", use_container_width=True):
                _start_quiz(topic, num_q, diff)


def _start_quiz(topic: str, num_q: int, difficulty: str):
    """Generate quiz questions and move to quiz phase."""
    from services.quiz_service import generate_quiz

    ai = _get_ai()
    rag = _get_rag()

    try:
        with st.spinner(f"🤖 Generating {num_q} questions..."):
            questions = generate_quiz(rag, ai, topic, num_q, difficulty)

        if not questions:
            st.error("⚠️ Could not generate questions. Try a different topic.")
            return

        st.session_state.quiz_questions = questions
        st.session_state.quiz_answers = {}
        st.session_state.quiz_current_q = 0
        st.session_state.quiz_topic = topic
        st.session_state.quiz_difficulty = difficulty
        st.session_state.quiz_num_questions = len(questions)
        st.session_state.quiz_phase = "quiz"
        st.rerun()

    except ConnectionError as e:
        st.error(f"🔌 {e}")
    except ValueError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        st.error(f"⚠️ Quiz generation failed: {e}")


# =========================================================================
# PHASE: Quiz
# =========================================================================

def _render_quiz():
    """Render question-by-question quiz interface."""
    questions = st.session_state.quiz_questions
    current = st.session_state.quiz_current_q
    total = len(questions)
    answers = st.session_state.quiz_answers

    if not questions:
        st.error("No questions loaded.")
        _reset_quiz()
        return

    # --- Progress bar ---
    answered_count = len(answers)
    progress = answered_count / total
    st.progress(progress, text=f"Question Progress: {answered_count}/{total} answered")

    # --- Question card ---
    q = questions[current]

    st.markdown(f"**Question {current + 1} of {total}**")
    if q.get("topic") and q["topic"] != "General":
        st.caption(f"Topic: {q['topic']} · Difficulty: {q.get('difficulty', 'Medium')}")

    with st.container(border=True):
        st.markdown(f"### {q['question']}")

        options = {
            "A": q["A"],
            "B": q["B"],
            "C": q["C"],
            "D": q["D"],
        }

        # Build radio options
        option_labels = [f"**{k}.** {v}" for k, v in options.items()]
        option_keys = list(options.keys())

        # Get current answer if exists
        current_answer = answers.get(current)
        default_index = option_keys.index(current_answer) if current_answer in option_keys else None

        selected = st.radio(
            "Select your answer:",
            options=option_keys,
            format_func=lambda k: f"{k}. {options[k]}",
            index=default_index,
            key=f"q_radio_{current}",
            label_visibility="collapsed",
        )

        # Save answer
        if selected:
            st.session_state.quiz_answers[current] = selected

    # --- Navigation ---
    nav_cols = st.columns([1, 1, 1, 1])

    with nav_cols[0]:
        if current > 0:
            if st.button("⬅️ Previous", key="prev_q", use_container_width=True):
                st.session_state.quiz_current_q = current - 1
                st.rerun()

    with nav_cols[1]:
        if current < total - 1:
            if st.button("Next ➡️", key="next_q", use_container_width=True):
                st.session_state.quiz_current_q = current + 1
                st.rerun()

    with nav_cols[3]:
        if answered_count == total:
            if st.button("📊 Submit Quiz", key="submit_quiz", use_container_width=True, type="primary"):
                _submit_quiz()
        else:
            unanswered = total - answered_count
            st.caption(f"{unanswered} question(s) unanswered")

    # --- Question navigator ---
    st.markdown("---")
    st.caption("Jump to question:")
    q_cols = st.columns(min(total, 10))
    for i in range(total):
        with q_cols[i % min(total, 10)]:
            label = f"{'✅' if i in answers else '⬜'} {i+1}"
            if st.button(label, key=f"jump_{i}", use_container_width=True):
                st.session_state.quiz_current_q = i
                st.rerun()


def _submit_quiz():
    """Score the quiz and move to result phase."""
    from services.quiz_service import score_quiz, detect_weak_topics, save_assessment_to_db

    result = score_quiz(
        st.session_state.quiz_questions,
        st.session_state.quiz_answers,
    )

    weak_topics = detect_weak_topics(result["topic_scores"])

    st.session_state.quiz_result = result
    st.session_state.quiz_weak_topics = weak_topics

    # Save to database
    save_assessment_to_db(
        quiz_result=result,
        topic=st.session_state.quiz_topic,
        difficulty=st.session_state.quiz_difficulty,
        pdf_name=st.session_state.get("pdf_name"),
    )

    st.session_state.quiz_phase = "result"
    st.rerun()


# =========================================================================
# PHASE: Result
# =========================================================================

def _render_result():
    """Render the result dashboard."""
    result = st.session_state.quiz_result
    weak = st.session_state.quiz_weak_topics

    if not result:
        _reset_quiz()
        return

    # --- Score display ---
    col_score, col_details = st.columns([1, 1])

    with col_score:
        with st.container(border=True):
            st.markdown(
                f'<div class="score-circle">'
                f'<div class="percentage">{result["percentage"]}%</div>'
                f'<div class="fraction">{result["correct"]} / {result["total"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_details:
        with st.container(border=True):
            st.markdown("#### 📊 Summary")
            st.markdown(f"✅ **Correct:** {result['correct']}")
            st.markdown(f"❌ **Incorrect:** {result['incorrect']}")
            st.markdown(f"📝 **Topic:** {st.session_state.quiz_topic}")
            st.markdown(f"⚙️ **Difficulty:** {st.session_state.quiz_difficulty}")

    # --- Topic performance ---
    if weak:
        st.markdown("---")
        st.markdown("### 📊 Learning Analysis")

        col_s, col_w = st.columns(2)

        with col_s:
            st.markdown("**Strong Areas**")
            if weak["strong"]:
                for t in weak["strong"]:
                    st.markdown(
                        f'<div class="topic-strong">✅ {t["topic"]} — '
                        f'{t["percentage"]}% ({t["correct"]}/{t["total"]})</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No strong areas yet")

        with col_w:
            st.markdown("**Needs Attention**")
            if weak["attention"]:
                for t in weak["attention"]:
                    st.markdown(
                        f'<div class="topic-attention">⚠️ {t["topic"]} — '
                        f'{t["percentage"]}% ({t["correct"]}/{t["total"]})</div>',
                        unsafe_allow_html=True,
                    )
            if weak["weak"]:
                for t in weak["weak"]:
                    st.markdown(
                        f'<div class="topic-weak">🔴 {t["topic"]} — '
                        f'{t["percentage"]}% ({t["correct"]}/{t["total"]})</div>',
                        unsafe_allow_html=True,
                    )
            if not weak["attention"] and not weak["weak"]:
                st.caption("Great job! No weak areas.")

    # --- Action buttons ---
    st.markdown("---")

    action_cols = st.columns(4)

    with action_cols[0]:
        if st.button("📋 Review Answers", key="go_review", use_container_width=True):
            st.session_state.quiz_phase = "review"
            st.rerun()

    with action_cols[1]:
        # Find weakest topic
        weakest = None
        if weak and (weak["weak"] or weak["attention"]):
            all_weak = weak["weak"] + weak["attention"]
            weakest = all_weak[0]["topic"] if all_weak else None

        if weakest:
            if st.button("🎯 Improve Weak Areas", key="go_practice", use_container_width=True, type="primary"):
                st.session_state.practice_topic = weakest
                st.session_state.practice_previous_pct = next(
                    (t["percentage"] for t in (weak["weak"] + weak["attention"]) if t["topic"] == weakest),
                    0
                )
                st.session_state.quiz_phase = "practice"
                st.rerun()

    with action_cols[2]:
        if st.button("🔄 Retake Assessment", key="retake", use_container_width=True):
            topic = st.session_state.quiz_topic
            diff = st.session_state.quiz_difficulty
            num = st.session_state.quiz_num_questions
            _reset_quiz()
            _start_quiz(topic, num, diff)

    with action_cols[3]:
        # AI Tutor link for weakest topic
        if weakest:
            if st.button(f"🤖 Learn with AI Tutor", key="go_tutor", use_container_width=True):
                st.session_state.student_section = "ai_tutor"
                st.session_state.current_mode = "teach"
                st.session_state.chat_history.append(
                    {"role": "user", "content": f"Teach me about {weakest} in detail"}
                )
                st.rerun()


# =========================================================================
# PHASE: Review
# =========================================================================

def _render_review():
    """Render per-question review with explanations."""
    result = st.session_state.quiz_result

    if not result:
        _reset_quiz()
        return

    st.markdown("### 📋 Answer Review")

    if st.button("⬅️ Back to Results", key="back_result"):
        st.session_state.quiz_phase = "result"
        st.rerun()

    st.markdown("---")

    for pq in result["per_question"]:
        idx = pq["index"]
        is_correct = pq["is_correct"]

        css_class = "review-correct" if is_correct else "review-wrong"
        icon = "✅" if is_correct else "❌"

        with st.container(border=True):
            st.markdown(f"**{icon} Question {idx + 1}** · {pq.get('topic', '')}")
            st.markdown(f"_{pq['question']}_")

            # Show options with highlighting
            for letter in ["A", "B", "C", "D"]:
                option_text = pq[letter]
                if letter == pq["correct_answer"] and letter == pq["student_answer"]:
                    st.markdown(f"✅ **{letter}. {option_text}** ← Your answer (Correct!)")
                elif letter == pq["correct_answer"]:
                    st.markdown(f"✅ **{letter}. {option_text}** ← Correct answer")
                elif letter == pq["student_answer"]:
                    st.markdown(f"❌ ~~{letter}. {option_text}~~ ← Your answer")
                else:
                    st.markdown(f"　{letter}. {option_text}")

            # Show explanation for wrong answers
            if not is_correct:
                # Check if we already generated an explanation
                if idx in st.session_state.quiz_explanations:
                    st.markdown("---")
                    st.markdown(st.session_state.quiz_explanations[idx])
                else:
                    if st.button(f"💡 Explain why", key=f"explain_{idx}"):
                        _generate_review_explanation(idx, pq)

                # Quick explanation from quiz data
                if pq.get("explanation"):
                    st.caption(f"📝 {pq['explanation']}")


def _generate_review_explanation(idx: int, pq: dict):
    """Generate and cache an AI explanation for a wrong answer."""
    from services.quiz_service import generate_explanation

    ai = _get_ai()
    rag = _get_rag()

    try:
        with st.spinner("💡 Generating explanation..."):
            explanation = generate_explanation(rag, ai, pq)
        st.session_state.quiz_explanations[idx] = explanation
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Could not generate explanation: {e}")


# =========================================================================
# PHASE: Practice (Adaptive)
# =========================================================================

def _render_practice():
    """Render adaptive practice: learn → practice → retest."""
    topic = st.session_state.practice_topic

    if not topic:
        st.session_state.quiz_phase = "result"
        st.rerun()
        return

    st.markdown(f"### 🎯 Improve: {topic}")
    st.caption("Adaptive Practice: Learn → Practice → Improve")

    if st.button("⬅️ Back to Results", key="back_from_practice"):
        st.session_state.quiz_phase = "result"
        st.rerun()

    st.markdown("---")

    # --- Step 1: Lesson ---
    if st.session_state.practice_lesson is None:
        if st.button(f"📖 Learn about {topic}", key="gen_lesson", use_container_width=True, type="primary"):
            _generate_lesson(topic)
        return

    # Show lesson
    with st.container(border=True):
        st.markdown(f"#### 📖 Quick Lesson: {topic}")
        st.markdown(st.session_state.practice_lesson)

    st.markdown("---")

    # --- Step 2: Practice questions ---
    if not st.session_state.practice_questions:
        if st.button(f"📝 Practice {topic} (3 questions)", key="gen_practice", use_container_width=True, type="primary"):
            _generate_practice(topic)
        return

    # --- Step 3: Show practice quiz or results ---
    if st.session_state.practice_result is None:
        _render_practice_quiz()
    else:
        _render_practice_result()


def _generate_lesson(topic: str):
    """Generate an adaptive lesson for the weak topic."""
    from services.quiz_service import generate_adaptive_lesson

    ai = _get_ai()
    rag = _get_rag()

    try:
        with st.spinner(f"📖 Preparing lesson on {topic}..."):
            lesson = generate_adaptive_lesson(rag, ai, topic)
        st.session_state.practice_lesson = lesson
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Could not generate lesson: {e}")


def _generate_practice(topic: str):
    """Generate practice questions for the weak topic."""
    from services.quiz_service import generate_practice_questions

    ai = _get_ai()
    rag = _get_rag()

    try:
        with st.spinner(f"📝 Generating practice questions on {topic}..."):
            questions = generate_practice_questions(rag, ai, topic, num_questions=3)

        if not questions:
            st.error("⚠️ Could not generate practice questions.")
            return

        st.session_state.practice_questions = questions
        st.session_state.practice_answers = {}
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Practice generation failed: {e}")


def _render_practice_quiz():
    """Render the practice mini-quiz."""
    questions = st.session_state.practice_questions
    answers = st.session_state.practice_answers

    st.markdown("#### 📝 Practice Quiz")

    for i, q in enumerate(questions):
        with st.container(border=True):
            st.markdown(f"**Practice Q{i + 1}.** {q['question']}")

            options = {"A": q["A"], "B": q["B"], "C": q["C"], "D": q["D"]}
            current_answer = answers.get(i)
            default_idx = list(options.keys()).index(current_answer) if current_answer in options else None

            selected = st.radio(
                f"Answer Q{i+1}:",
                options=list(options.keys()),
                format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                index=default_idx,
                key=f"practice_radio_{i}",
                label_visibility="collapsed",
            )

            if selected:
                st.session_state.practice_answers[i] = selected

    # Submit practice
    if len(answers) == len(questions):
        if st.button("📊 Submit Practice", key="submit_practice", use_container_width=True, type="primary"):
            _submit_practice()
    else:
        st.caption(f"{len(questions) - len(answers)} question(s) unanswered")


def _submit_practice():
    """Score the practice quiz and show improvement."""
    from services.quiz_service import score_quiz

    result = score_quiz(
        st.session_state.practice_questions,
        st.session_state.practice_answers,
    )

    st.session_state.practice_result = result
    st.rerun()


def _render_practice_result():
    """Show practice results with improvement comparison."""
    result = st.session_state.practice_result
    previous = st.session_state.practice_previous_pct
    topic = st.session_state.practice_topic

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### 📊 Practice Result")
            st.markdown(
                f'<div class="score-circle">'
                f'<div class="percentage">{result["percentage"]}%</div>'
                f'<div class="fraction">{result["correct"]} / {result["total"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col2:
        with st.container(border=True):
            st.markdown(f"#### 📈 {topic} Progress")

            if previous is not None:
                improvement = result["percentage"] - previous
                st.markdown(f"**Previous:** {previous}%")
                st.markdown(f"**Now:** {result['percentage']}%")

                if improvement > 0:
                    st.markdown(
                        f'<span class="improvement-badge">📈 +{improvement:.0f}% Improvement!</span>',
                        unsafe_allow_html=True,
                    )
                    st.balloons()
                elif improvement == 0:
                    st.info("Same score — keep practicing!")
                else:
                    st.warning("Score decreased — review the lesson again.")

    # Show correct/incorrect for each practice question
    st.markdown("---")
    for pq in result["per_question"]:
        icon = "✅" if pq["is_correct"] else "❌"
        st.markdown(f"{icon} {pq['question']}")
        if not pq["is_correct"]:
            st.caption(f"Your answer: {pq['student_answer']} · Correct: {pq['correct_answer']}")
            if pq.get("explanation"):
                st.caption(f"💡 {pq['explanation']}")

    # Actions
    st.markdown("---")
    action_cols = st.columns(3)

    with action_cols[0]:
        if st.button(f"🔄 Retest {topic}", key="retest_topic", use_container_width=True):
            # Reset practice but keep lesson
            st.session_state.practice_previous_pct = result["percentage"]
            st.session_state.practice_questions = []
            st.session_state.practice_answers = {}
            st.session_state.practice_result = None
            st.rerun()

    with action_cols[1]:
        if st.button("⬅️ Back to Results", key="back_from_practice_result", use_container_width=True):
            st.session_state.quiz_phase = "result"
            st.rerun()

    with action_cols[2]:
        if st.button("🆕 New Assessment", key="new_assessment_practice", use_container_width=True):
            _reset_quiz()
            st.rerun()


# =========================================================================
# Main entry point
# =========================================================================

def show():
    """Render the Assessment section."""
    _init_assessment_state()
    st.markdown(ASSESSMENT_CSS, unsafe_allow_html=True)

    # --- Header ---
    st.markdown(
        '<div class="hero-header" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">'
        '<h1>📝 AI Assessment</h1>'
        '<p>Test your understanding and discover what to improve</p></div>',
        unsafe_allow_html=True,
    )

    # Route to current phase
    phase = st.session_state.quiz_phase

    if phase == "setup":
        _render_setup()
    elif phase == "quiz":
        _render_quiz()
    elif phase == "result":
        _render_result()
    elif phase == "review":
        _render_review()
    elif phase == "practice":
        _render_practice()
    else:
        _render_setup()
