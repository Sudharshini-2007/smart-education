"""
pages/teacher.py - Teacher Classroom Intelligence Dashboard.

Provides:
- Summary cards (students, assignments, class average, attention)
- Student management (add/view/remove)
- Assignment creation and management
- Class performance analytics (topic-wise from real assessment data)
- AI Classroom Insight
- Students needing support
- Targeted teacher actions
"""

import streamlit as st
from datetime import date, timedelta

# =========================================================================
# Custom CSS
# =========================================================================

TEACHER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.teacher-stat {
    background: white;
    border: 1px solid #e0e3e8;
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
    font-family: 'Inter', sans-serif;
}
.teacher-stat .stat-val {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.teacher-stat .stat-lbl {
    font-size: 0.85rem;
    color: #777;
    margin-top: 0.2rem;
}
.insight-box {
    background: linear-gradient(135deg, #e8eaf6, #c5cae9);
    border: 1px solid #9fa8da;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    margin: 1rem 0;
    font-family: 'Inter', sans-serif;
}
.attention-card {
    background: linear-gradient(135deg, #fff3e0, #ffe0b2);
    border: 1px solid #ffb74d;
    border-radius: 14px;
    padding: 1rem 1.3rem;
    margin: 0.5rem 0;
    font-family: 'Inter', sans-serif;
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
</style>
"""

# =========================================================================
# Session state
# =========================================================================

def _init_teacher_state():
    defaults = {
        "teacher_tab": "overview",
        "classroom_insight": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _get_ai():
    if st.session_state.get("ai_service") is None:
        from services.ai_service import AIService
        st.session_state.ai_service = AIService()
    return st.session_state.ai_service


# =========================================================================
# Main entry
# =========================================================================

def show():
    """Render the Teacher Dashboard."""
    _init_teacher_state()
    st.markdown(TEACHER_CSS, unsafe_allow_html=True)

    # --- Header ---
    st.markdown(
        '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
        'color: white; border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;">'
        '<h1 style="margin:0; font-family: Inter, sans-serif;">🏫 Classroom Intelligence</h1>'
        '<p style="margin:0.3rem 0 0; opacity:0.9;">Understand your class. Identify learning gaps. Take action.</p>'
        '</div>',
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

    # --- Summary cards ---
    _render_summary_cards()

    # --- Sidebar navigation ---
    _render_sidebar()

    section = st.session_state.teacher_tab

    if section == "overview":
        _render_overview()
    elif section == "students":
        _render_students()
    elif section == "assignments":
        _render_assignments()
    elif section == "performance":
        _render_performance()
    elif section == "insights":
        _render_ai_insight()
    else:
        _render_overview()


def _render_sidebar():
    """Add teacher-specific navigation items to the sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("#### 🏫 Teacher Menu")

        nav_items = [
            ("📊 Classroom Overview", "overview"),
            ("👥 Students", "students"),
            ("📝 Assignments", "assignments"),
            ("📈 Class Performance", "performance"),
            ("🧠 AI Classroom Insights", "insights"),
        ]

        for label, key in nav_items:
            is_active = st.session_state.teacher_tab == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
                st.session_state.teacher_tab = key
                st.rerun()


# =========================================================================
# Summary cards
# =========================================================================

def _render_summary_cards():
    from services.classroom_service import (
        get_student_count, get_active_assignment_count,
        get_class_average, get_students_needing_support,
    )

    total_students = get_student_count()
    active_assignments = get_active_assignment_count()
    class_avg = get_class_average()
    support_count = len(get_students_needing_support())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="teacher-stat"><div class="stat-val">👥 {total_students}</div>'
            f'<div class="stat-lbl">Total Students</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="teacher-stat"><div class="stat-val">📝 {active_assignments}</div>'
            f'<div class="stat-lbl">Active Assignments</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        avg_display = f"{class_avg}%" if class_avg is not None else "—"
        st.markdown(
            f'<div class="teacher-stat"><div class="stat-val">📊 {avg_display}</div>'
            f'<div class="stat-lbl">Class Average</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="teacher-stat"><div class="stat-val">⚠️ {support_count}</div>'
            f'<div class="stat-lbl">Need Attention</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("")


# =========================================================================
# Overview tab — Class Performance + Students Needing Support
# =========================================================================

def _render_overview():
    from services.classroom_service import get_topic_performance, get_students_needing_support

    # --- Students needing support ---
    st.markdown("### ⚠️ Students Needing Additional Support")
    struggling = get_students_needing_support()

    if not struggling:
        st.success("🎉 No students are currently flagged. All students are performing well or there isn't enough data yet.")
    else:
        for s in struggling[:10]:
            weak_info = ""
            if s.get("weakest_pct") is not None:
                weak_info = f" ({s['weakest_pct']}%)"
            st.markdown(
                f'<div class="attention-card">'
                f'<strong>{s["name"]}</strong><br>'
                f'<small>'
                f'Average: {s["avg_score"]}% · '
                f'Weakest: {s["weakest_topic"] or "—"}{weak_info}'
                f'<br>💬 Needs additional support</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # --- Quick actions ---
    st.markdown("---")
    st.markdown("### 🎯 Targeted Teacher Actions")

    topic_perf = get_topic_performance()
    # Identify weakest topic
    weakest_topic = None
    if topic_perf:
        weakest = min(topic_perf.items(), key=lambda x: x[1]["percentage"])
        if weakest[1]["percentage"] < 70:
            weakest_topic = weakest[0]

    if weakest_topic:
        st.info(f"💡 Most students are struggling with **{weakest_topic}**. Take targeted action:")
        act1, act2 = st.columns(2)
        with act1:
            if st.button("📝 Create Practice Quiz", key="quick_practice", use_container_width=True):
                st.session_state.teacher_tab = "assignments"
                st.session_state.prefill_assignment = {
                    "title": f"Practice Quiz: {weakest_topic}",
                    "description": f"Please use the Assessment tool to take a Practice Quiz on {weakest_topic}.",
                    "topic": weakest_topic
                }
                st.rerun()
        with act2:
            if st.button("📝 Create Assignment", key="quick_assignment_weak", use_container_width=True):
                st.session_state.teacher_tab = "assignments"
                st.session_state.prefill_assignment = {
                    "title": f"Assignment: {weakest_topic}",
                    "description": f"Please complete the following assignment on {weakest_topic}.",
                    "topic": weakest_topic
                }
                st.rerun()
    else:
        act1, act2 = st.columns(2)
        with act1:
            if st.button("📝 Create Assignment", key="quick_assignment", use_container_width=True):
                st.session_state.teacher_tab = "assignments"
                st.rerun()
        with act2:
            if st.button("🧠 Get AI Classroom Insight", key="quick_insight", use_container_width=True):
                st.session_state.teacher_tab = "insights"
                st.rerun()


# =========================================================================
# Class Performance tab
# =========================================================================

def _render_performance():
    from services.classroom_service import get_topic_performance

    st.markdown("### 📈 Topic-wise Class Performance")

    topic_perf = get_topic_performance()
    if not topic_perf:
        st.info("📭 No assessment data yet. Performance analytics will appear after students take assessments.")
    else:
        for topic, data in sorted(topic_perf.items(), key=lambda x: x[1]["percentage"], reverse=True):
            pct = data["percentage"]
            icon = "🟢" if pct >= 70 else ("🟠" if pct >= 40 else "🔴")
            col_name, col_bar, col_pct = st.columns([2, 4, 1])
            with col_name:
                st.markdown(f"**{topic}**")
            with col_bar:
                st.progress(pct / 100, text="")
            with col_pct:
                st.markdown(f"{icon} {pct}%")


# =========================================================================
# Students tab
# =========================================================================

def _render_students():
    from services.classroom_service import get_students, add_student, remove_student

    st.markdown("### 👥 Student Management")

    # Add student form
    with st.expander("➕ Add a Student", expanded=False):
        with st.form("add_student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name", placeholder="Enter student name")
            with col2:
                email = st.text_input("Email", placeholder="student@example.com")
            submitted = st.form_submit_button("Add Student", use_container_width=True)

            if submitted:
                if not name or not email:
                    st.error("Please enter both name and email.")
                elif "@" not in email:
                    st.error("Please enter a valid email address.")
                else:
                    sid = add_student(name.strip(), email.strip())
                    if sid:
                        st.success(f"✅ Added **{name}** successfully!")
                        st.rerun()
                    else:
                        st.error("⚠️ Could not add student. Email may already exist.")

    st.markdown("")

    # Student list
    students = get_students()
    if not students:
        st.info("📭 No students enrolled yet. Add students using the form above.")
        return

    st.caption(f"Total: {len(students)} students")

    for student in students:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(f"**{student['name']}**")
                st.caption(student["email"])
            with c2:
                st.caption(f"Enrolled: {student['created_at'][:10] if student['created_at'] else '—'}")
            with c3:
                if st.button("🗑️", key=f"rm_student_{student['id']}", help="Remove student"):
                    remove_student(student["id"])
                    st.rerun()


# =========================================================================
# Assignments tab
# =========================================================================

def _render_assignments():
    from services.classroom_service import (
        get_assignments, create_assignment, get_assignment_submissions,
    )

    st.markdown("### 📝 Assignment Management")

    # Handle prefill from targeted actions
    prefill = None
    if "prefill_assignment" in st.session_state:
        prefill = st.session_state.prefill_assignment
        del st.session_state.prefill_assignment
        st.session_state.create_title = prefill["title"]
        st.session_state.create_desc = prefill["description"]
        st.session_state.create_topic = prefill["topic"]

    # Create assignment form
    with st.expander("➕ Create Assignment", expanded=True if prefill else False):
        with st.form("create_assignment_form", clear_on_submit=True):
            title = st.text_input("Title", key="create_title", placeholder="Assignment title")
            description = st.text_area("Description", key="create_desc", placeholder="What should students do?", height=100)
            col1, col2 = st.columns(2)
            with col1:
                topic = st.text_input("Topic", key="create_topic", placeholder="e.g., Graph Traversal")
            with col2:
                deadline = st.date_input(
                    "Deadline",
                    value=date.today() + timedelta(days=7),
                    min_value=date.today(),
                )
            submitted = st.form_submit_button("Create Assignment", use_container_width=True)

            if submitted:
                if not title:
                    st.error("Please enter a title.")
                else:
                    aid = create_assignment(
                        title=title.strip(),
                        description=description.strip(),
                        topic=topic.strip() if topic else "General",
                        deadline=deadline.isoformat(),
                    )
                    if aid:
                        st.success(f"✅ Assignment **{title}** created!")
                        st.rerun()
                    else:
                        st.error("⚠️ Could not create assignment.")

    st.markdown("")

    # Assignment list
    assignments = get_assignments()
    if not assignments:
        st.info("📭 No assignments yet. Create one using the form above.")
        return

    for a in assignments:
        with st.container(border=True):
            header_col, status_col = st.columns([4, 1])
            with header_col:
                active_badge = "🟢 Active" if a["is_active"] else "⚪ Closed"
                st.markdown(f"**{a['title']}** {active_badge}")
                if a["description"]:
                    st.caption(a["description"][:150])
                st.caption(f"📌 {a['topic'] or 'General'} · 📅 Due: {a['deadline'] or '—'} · 📬 {a['submission_count']} submissions")

            with status_col:
                if st.button("📬 View", key=f"view_subs_{a['id']}", use_container_width=True):
                    st.session_state[f"show_subs_{a['id']}"] = not st.session_state.get(f"show_subs_{a['id']}", False)
                    st.rerun()

            # Show submissions
            if st.session_state.get(f"show_subs_{a['id']}", False):
                subs = get_assignment_submissions(a["id"])
                if not subs:
                    st.caption("No submissions yet.")
                else:
                    for sub in subs:
                        st.markdown(
                            f"&nbsp;&nbsp;&nbsp;&nbsp;📄 **{sub['student_name']}** — "
                            f"submitted {sub['submitted_at'][:16] if sub['submitted_at'] else '—'}"
                        )
                        if sub["content"]:
                            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{sub['content'][:200]}")


# =========================================================================
# AI Insight tab
# =========================================================================

def _render_ai_insight():
    from services.classroom_service import generate_classroom_insight

    st.markdown("### 🧠 AI Classroom Insight")
    st.caption("AI analyzes your class data and provides actionable recommendations.")

    ai = _get_ai()
    ai_ok = ai.check_available()

    if not ai_ok:
        st.warning("⚠️ **AI is unavailable.** Start Ollama with `ollama serve` to generate insights.")

    # Show cached insight
    if st.session_state.classroom_insight:
        st.markdown(
            f'<div class="insight-box">{st.session_state.classroom_insight}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "🧠 Generate AI Insight" if not st.session_state.classroom_insight else "🔄 Refresh Insight",
            key="gen_class_insight",
            use_container_width=True,
            type="primary",
        ):
            try:
                with st.spinner("🧠 Analyzing class data..."):
                    insight = generate_classroom_insight(ai)
                st.session_state.classroom_insight = insight
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Could not generate insight: {e}")

    with col2:
        if st.session_state.classroom_insight:
            if st.button("🗑️ Clear", key="clear_insight", use_container_width=True):
                st.session_state.classroom_insight = None
                st.rerun()

    # --- Data summary (always visible) ---
    st.markdown("---")
    st.markdown("### 📋 Raw Class Data")

    from services.classroom_service import (
        get_student_count, get_class_average, get_topic_performance,
        get_active_assignment_count,
    )

    data_cols = st.columns(2)
    with data_cols[0]:
        with st.container(border=True):
            st.markdown("**📊 Assessment Data**")
            avg = get_class_average()
            if avg is not None:
                st.markdown(f"Class Average: **{avg}%**")
                topic_perf = get_topic_performance()
                if topic_perf:
                    for topic, data in sorted(topic_perf.items(), key=lambda x: x[1]["percentage"]):
                        icon = "🟢" if data["percentage"] >= 70 else ("🟠" if data["percentage"] >= 40 else "🔴")
                        st.caption(f"{icon} {topic}: {data['percentage']}%")
            else:
                st.caption("No assessment data yet.")

    with data_cols[1]:
        with st.container(border=True):
            st.markdown("**📝 Classroom Data**")
            st.caption(f"Students: {get_student_count()}")
            st.caption(f"Active Assignments: {get_active_assignment_count()}")
