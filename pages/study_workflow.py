"""
pages/study_workflow.py - Adaptive AI Study Workflow.

Provides:
- Study plan setup (exam date, daily hours, preference)
- AI-generated multi-day study plan
- Daily task dashboard with checkboxes
- Progress tracking and study streak
- Adaptive rescheduling for incomplete tasks
- AI learning insights
- Integration with AI Tutor and Assessment
"""

import streamlit as st
from datetime import date, timedelta

# =========================================================================
# Custom CSS
# =========================================================================

STUDY_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ---------- Streak badge ---------- */
.streak-badge {
    background: linear-gradient(135deg, #ff9a56, #ff6f61);
    color: white;
    padding: 0.6rem 1.4rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
    font-family: 'Inter', sans-serif;
}

/* ---------- Day card ---------- */
.day-card {
    background: linear-gradient(135deg, #f8f9fb, #eef1f6);
    border: 1px solid #dde1e8;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin: 0.6rem 0;
    font-family: 'Inter', sans-serif;
}
.day-card.today {
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    border-color: #64b5f6;
    border-width: 2px;
}
.day-card h4 {
    margin: 0 0 0.5rem 0;
    font-family: 'Inter', sans-serif;
}

/* ---------- Stat card ---------- */
.stat-card {
    background: white;
    border: 1px solid #e0e3e8;
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
    font-family: 'Inter', sans-serif;
}
.stat-card .stat-value {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-card .stat-label {
    font-size: 0.85rem;
    color: #777;
    margin-top: 0.2rem;
}

/* ---------- Insight card ---------- */
.insight-card {
    background: linear-gradient(135deg, #e8eaf6, #c5cae9);
    border: 1px solid #9fa8da;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
    font-family: 'Inter', sans-serif;
}

/* ---------- Task type badges ---------- */
.task-learn { color: #2e7d32; font-weight: 600; }
.task-practice { color: #e65100; font-weight: 600; }
.task-review { color: #1565c0; font-weight: 600; }
</style>
"""


# =========================================================================
# Session state
# =========================================================================

def _init_study_state():
    """Initialise study workflow session state."""
    defaults = {
        "study_phase": "auto",       # auto | setup | dashboard | plan_view
        "study_topics": [],          # extracted topics
        "study_plan_data": None,     # raw plan data
        "study_insight": None,       # AI insight text
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# =========================================================================
# Service access helpers
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
# Auto-detect phase
# =========================================================================

def _detect_phase() -> str:
    """Determine which phase to show based on existing data."""
    from services.study_service import get_active_plan

    plan = get_active_plan()
    if plan:
        return "dashboard"
    return "setup"


# =========================================================================
# PHASE: Setup
# =========================================================================

def _render_setup():
    """Render study plan setup form."""

    # Check prerequisites
    has_pdf = bool(st.session_state.get("pdf_name"))
    ai = _get_ai()
    ai_ok = ai.check_available()

    if not has_pdf:
        st.info(
            "📄 **Upload study material first.**\n\n"
            "Go to 🧠 AI Tutor, upload a PDF, then return here to create your study plan.\n\n"
            "Your plan will be much better when it's based on your actual study material."
        )

    if not ai_ok:
        st.warning(
            "⚠️ **AI is unavailable.** Ollama is not running.\n\n"
            "Start it with `ollama serve` to generate study plans.",
            icon="🔌",
        )

    # Check for assessment data
    from services.study_service import get_assessment_topic_scores
    topic_scores = get_assessment_topic_scores()

    if topic_scores:
        with st.container(border=True):
            st.markdown("#### 📊 Your Assessment Data")
            st.caption("Your study plan will prioritize weak areas.")
            for topic, data in sorted(topic_scores.items(), key=lambda x: x[1]["percentage"]):
                icon = "✅" if data["percentage"] >= 70 else ("⚠️" if data["percentage"] >= 40 else "🔴")
                st.markdown(f"{icon} **{topic}** — {data['percentage']}%")
    else:
        st.caption("💡 No assessment data yet. Take an assessment first for a smarter plan, or create a basic plan now.")

    st.markdown("---")

    # --- Setup form ---
    with st.container(border=True):
        st.markdown("#### 📅 Plan Your Studies")

        col1, col2 = st.columns(2)

        with col1:
            exam_date = st.date_input(
                "Exam Date",
                value=date.today() + timedelta(days=7),
                min_value=date.today() + timedelta(days=1),
                key="setup_exam_date",
            )

            daily_hours = st.select_slider(
                "Available study time per day",
                options=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
                value=2.0,
                format_func=lambda x: f"{x:.0f} hour{'s' if x != 1 else ''}" if x == int(x) else f"{x} hours",
                key="setup_daily_hours",
            )

        with col2:
            preference = st.radio(
                "Study preference",
                options=["Learn concepts", "Practice questions", "Balanced"],
                index=2,
                key="setup_preference",
            )

            # Topic selection if PDF is loaded
            if has_pdf and not st.session_state.study_topics:
                if st.button("🔍 Extract Topics from Material", key="extract_topics"):
                    _extract_topics()

            if st.session_state.study_topics:
                selected_topics = st.multiselect(
                    "Select topics to focus on",
                    options=st.session_state.study_topics,
                    default=st.session_state.study_topics,
                    key="setup_selected_topics",
                )
            else:
                selected_topics = list(topic_scores.keys()) if topic_scores else []

        st.markdown("")

        if st.button("🚀 Generate Study Plan", key="gen_plan", use_container_width=True, type="primary"):
            if not ai_ok:
                st.error("⚠️ Cannot generate plan — AI is unavailable.")
                return

            topics = selected_topics or st.session_state.study_topics or list(topic_scores.keys()) or ["General"]
            _generate_plan(
                topics=topics,
                topic_scores=topic_scores,
                exam_date=exam_date.isoformat(),
                daily_hours=daily_hours,
                preference=preference,
            )


def _extract_topics():
    """Extract topics from uploaded material using AI."""
    from services.study_service import extract_topics_from_chunks

    chunks = st.session_state.get("pdf_chunks", [])
    ai = _get_ai()

    try:
        with st.spinner("🔍 Analyzing study material..."):
            topics = extract_topics_from_chunks(chunks, ai)
        st.session_state.study_topics = topics
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Could not extract topics: {e}")


def _generate_plan(topics, topic_scores, exam_date, daily_hours, preference):
    """Generate a study plan and save to DB."""
    from services.study_service import generate_study_plan, save_plan_to_db

    ai = _get_ai()
    rag = _get_rag()

    weak_topics = {}
    if topic_scores:
        weak_topics = {t: d["percentage"] for t, d in topic_scores.items()}

    try:
        with st.spinner("🤖 Creating your personalized study plan..."):
            plan_data = generate_study_plan(
                topics=topics,
                weak_topics=weak_topics,
                exam_date_str=exam_date,
                daily_hours=daily_hours,
                preference=preference,
                rag_service=rag,
                ai_service=ai,
            )

        if not plan_data:
            st.error("⚠️ Could not generate a study plan. Please try again.")
            return

        plan_id = save_plan_to_db(
            plan_data=plan_data,
            exam_date=exam_date,
            daily_hours=daily_hours,
            preference=preference,
            pdf_name=st.session_state.get("pdf_name"),
        )

        if plan_id:
            st.session_state.study_phase = "dashboard"
            st.session_state.study_plan_data = plan_data
            st.session_state.study_insight = None
            st.rerun()
        else:
            st.error("⚠️ Could not save the plan. Please try again.")

    except ConnectionError as e:
        st.error(f"🔌 {e}")
    except Exception as e:
        st.error(f"⚠️ Plan generation failed: {e}")


# =========================================================================
# PHASE: Dashboard
# =========================================================================

def _render_dashboard():
    """Render the daily study dashboard."""
    from services.study_service import (
        get_active_plan, get_today_tasks, get_study_streak,
        reschedule_incomplete, get_progress_summary,
        get_assessment_topic_scores, generate_learning_insight,
    )

    plan = get_active_plan()
    if not plan:
        st.session_state.study_phase = "setup"
        st.rerun()
        return

    # Reschedule incomplete tasks from past days
    rescheduled = reschedule_incomplete(plan["id"])
    if rescheduled > 0:
        st.info(f"🔄 **Plan Adapted:** {rescheduled} unfinished task(s) moved to today.")
        plan = get_active_plan()  # reload after reschedule

    # Get today's data
    today_result = get_today_tasks(plan["id"])
    today_tasks, current_day = today_result if isinstance(today_result, tuple) else (today_result, 1)
    streak = get_study_streak()
    summary = get_progress_summary()

    # --- Top stats row ---
    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">📅 {current_day}/{plan["num_days"]}</div>'
            f'<div class="stat-label">Day</div></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">🔥 {streak}</div>'
            f'<div class="stat-label">Study Streak</div></div>',
            unsafe_allow_html=True,
        )
    with s3:
        avg = summary.get("assessment_avg")
        avg_display = f"{avg}%" if avg is not None else "—"
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">🎯 {avg_display}</div>'
            f'<div class="stat-label">Assessment Avg</div></div>',
            unsafe_allow_html=True,
        )
    with s4:
        priority = summary.get("priority_topic", "—")
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value">⚠️</div>'
            f'<div class="stat-label">Priority: {priority}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # --- Today's tasks ---
    st.markdown(f"### 🌅 Today's Learning — Day {current_day}")

    if today_tasks:
        completed = sum(1 for t in today_tasks if t["is_completed"])
        total = len(today_tasks)
        progress = completed / total if total > 0 else 0

        st.progress(progress, text=f"Today's Progress: {completed}/{total} tasks")

        # Calculate today's main topic
        topics_today = list(set(t["topic"] for t in today_tasks))
        st.caption(f"🎯 Main Goal: {', '.join(topics_today)}")

        for task in today_tasks:
            _render_task_checkbox(task)

        # Total study time
        total_min = sum(t["duration"] for t in today_tasks)
        done_min = sum(t["duration"] for t in today_tasks if t["is_completed"])
        st.caption(f"⏱️ {done_min}/{total_min} minutes completed")

    else:
        if current_day > plan["num_days"]:
            st.success("🎉 **Congratulations!** You've completed your study plan!")
        else:
            st.info("No tasks scheduled for today.")

    # --- Action buttons ---
    st.markdown("---")
    act_cols = st.columns(4)

    with act_cols[0]:
        if st.button("📋 View Full Plan", key="view_plan", use_container_width=True):
            st.session_state.study_phase = "plan_view"
            st.rerun()

    with act_cols[1]:
        if st.button("🤖 Learn with AI Tutor", key="go_tutor_from_study", use_container_width=True):
            # Navigate to AI Tutor with the priority topic
            priority = summary.get("priority_topic")
            st.session_state.student_section = "ai_tutor"
            if priority:
                st.session_state.current_mode = "teach"
            st.rerun()

    with act_cols[2]:
        if st.button("📝 Take Assessment", key="go_assess_from_study", use_container_width=True):
            st.session_state.student_section = "assessment"
            st.rerun()

    with act_cols[3]:
        if st.button("🆕 New Plan", key="new_plan", use_container_width=True):
            st.session_state.study_phase = "setup"
            st.session_state.study_insight = None
            st.rerun()

    # --- AI Learning Insight ---
    st.markdown("---")
    st.markdown("### 🧠 AI Learning Insight")

    topic_scores = get_assessment_topic_scores()

    if st.session_state.study_insight:
        st.markdown(
            f'<div class="insight-card">{st.session_state.study_insight}</div>',
            unsafe_allow_html=True,
        )
    else:
        if topic_scores or today_tasks:
            if st.button("💡 Get AI Recommendation", key="gen_insight", use_container_width=True):
                _generate_insight(topic_scores, plan)
        else:
            st.caption("Take an assessment to get personalized AI insights.")


def _render_task_checkbox(task: dict):
    """Render a single task with checkbox."""
    from services.study_service import mark_task_complete, mark_task_incomplete

    type_icons = {"learn": "📖", "practice": "✏️", "review": "🔄"}
    type_colors = {"learn": "task-learn", "practice": "task-practice", "review": "task-review"}
    icon = type_icons.get(task["type"], "📌")
    color_class = type_colors.get(task["type"], "")

    col_check, col_info, col_time = st.columns([0.5, 4, 1])

    with col_check:
        checked = st.checkbox(
            "done",
            value=task["is_completed"],
            key=f"task_check_{task['id']}",
            label_visibility="collapsed",
        )

    with col_info:
        desc = task.get("description") or f"{task['type'].capitalize()} {task['topic']}"
        if task["is_completed"]:
            st.markdown(f"~~{icon} {desc}~~")
        else:
            st.markdown(f"{icon} **{desc}**")
        st.caption(f"{task['topic']} · {task['type'].capitalize()}")

    with col_time:
        st.caption(f"{task['duration']} min")

    # Handle checkbox state changes
    if checked and not task["is_completed"]:
        mark_task_complete(task["id"])
        st.rerun()
    elif not checked and task["is_completed"]:
        mark_task_incomplete(task["id"])
        st.rerun()


def _generate_insight(topic_scores, plan_info):
    """Generate and cache an AI learning insight."""
    from services.study_service import generate_learning_insight

    ai = _get_ai()
    rag = _get_rag()

    try:
        with st.spinner("🧠 Analyzing your learning data..."):
            insight = generate_learning_insight(
                rag_service=rag,
                ai_service=ai,
                topic_scores=topic_scores,
                plan_info=plan_info,
                material_topics=st.session_state.get("study_topics", []),
            )
        st.session_state.study_insight = insight
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Could not generate insight: {e}")


# =========================================================================
# PHASE: Plan View
# =========================================================================

def _render_plan_view():
    """Render the full multi-day plan overview."""
    from services.study_service import get_active_plan

    plan = get_active_plan()
    if not plan:
        st.session_state.study_phase = "setup"
        st.rerun()
        return

    if st.button("⬅️ Back to Dashboard", key="back_dash"):
        st.session_state.study_phase = "dashboard"
        st.rerun()

    st.markdown("---")

    # Plan metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"📅 **Exam:** {plan.get('exam_date', '—')}")
    with col2:
        st.markdown(f"⏰ **Daily:** {plan.get('daily_hours', 2)} hours")
    with col3:
        st.markdown(f"📚 **Preference:** {plan.get('preference', 'Balanced')}")

    st.markdown("---")

    # Calculate current day
    from datetime import datetime as dt
    try:
        plan_start_str = plan.get("created_at", "")
        plan_start = dt.fromisoformat(plan_start_str).date() if plan_start_str else date.today()
    except (ValueError, TypeError):
        plan_start = date.today()
    current_day = max(1, (date.today() - plan_start).days + 1)

    # Day-by-day view
    for day_num, day_data in sorted(plan.get("days", {}).items()):
        is_today = (int(day_num) == current_day)
        is_past = (int(day_num) < current_day)

        css_class = "day-card today" if is_today else "day-card"
        day_label = f"Day {day_num}" + (" — 📍 TODAY" if is_today else ("  ✓" if is_past else ""))

        with st.container(border=True):
            st.markdown(f"#### {day_label}")

            tasks = day_data.get("tasks", [])
            completed = sum(1 for t in tasks if t.get("is_completed"))
            total = len(tasks)

            if total > 0:
                st.progress(completed / total, text=f"{completed}/{total} completed")

            for task in tasks:
                type_icons = {"learn": "📖", "practice": "✏️", "review": "🔄"}
                icon = type_icons.get(task.get("type", ""), "📌")
                done = "✅" if task.get("is_completed") else "⬜"
                desc = task.get("description", task.get("topic", ""))
                st.markdown(f"{done} {icon} {desc} — {task.get('duration', 30)} min")


# =========================================================================
# Main entry point
# =========================================================================

def show():
    """Render the Study Workflow section."""
    _init_study_state()
    st.markdown(STUDY_CSS, unsafe_allow_html=True)

    # --- Header ---
    st.markdown(
        '<div class="hero-header" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">'
        '<h1>📚 Your Smart Study Plan</h1>'
        '<p>Your plan adapts as you learn</p></div>',
        unsafe_allow_html=True,
    )

    # Auto-detect phase on first load
    phase = st.session_state.study_phase
    if phase == "auto":
        phase = _detect_phase()
        st.session_state.study_phase = phase

    # Route to current phase
    if phase == "setup":
        _render_setup()
    elif phase == "dashboard":
        _render_dashboard()
    elif phase == "plan_view":
        _render_plan_view()
    else:
        _render_setup()
