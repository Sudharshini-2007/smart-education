"""
pages/skill_journey.py - AI Skill Development / Skill Journey.

Provides:
- Career goal selection (presets + custom)
- Level selection and weekly hours
- AI-generated structured skill roadmap
- Per-skill progress tracking with status badges
- Personalized AI recommendations using assessment data
- Learning actions linked to AI Tutor and Assessment
- Project challenges per skill
- Next-step recommendation
"""

import streamlit as st

# =========================================================================
# Custom CSS
# =========================================================================

SKILL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ---------- Roadmap card ---------- */
.roadmap-card {
    background: white;
    border: 1px solid #e0e3e8;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    margin: 0.5rem 0;
    font-family: 'Inter', sans-serif;
    position: relative;
    transition: box-shadow 0.2s;
}
.roadmap-card:hover {
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}
.roadmap-card.completed {
    background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
    border-color: #a5d6a7;
}
.roadmap-card.learning {
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    border-color: #64b5f6;
}

/* ---------- Step number ---------- */
.step-number {
    display: inline-block;
    width: 32px;
    height: 32px;
    line-height: 32px;
    text-align: center;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    font-weight: 700;
    font-size: 0.9rem;
    margin-right: 0.6rem;
    font-family: 'Inter', sans-serif;
}
.step-number.done {
    background: linear-gradient(135deg, #43a047, #66bb6a);
}
.step-number.active {
    background: linear-gradient(135deg, #1e88e5, #42a5f5);
}

/* ---------- Goal card ---------- */
.goal-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin-bottom: 1rem;
    font-family: 'Inter', sans-serif;
}
.goal-card h3 {
    margin: 0;
    font-size: 1.3rem;
}
.goal-card .meta {
    opacity: 0.85;
    font-size: 0.95rem;
    margin-top: 0.3rem;
}

/* ---------- Status badge ---------- */
.status-not-started { color: #9e9e9e; font-weight: 600; }
.status-learning { color: #1e88e5; font-weight: 600; }
.status-completed { color: #43a047; font-weight: 600; }

/* ---------- Next step card ---------- */
.next-step-card {
    background: linear-gradient(135deg, #fff3e0, #ffe0b2);
    border: 1px solid #ffb74d;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
    font-family: 'Inter', sans-serif;
}

/* ---------- Recommendation card ---------- */
.rec-card {
    background: linear-gradient(135deg, #e8eaf6, #c5cae9);
    border: 1px solid #9fa8da;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
    font-family: 'Inter', sans-serif;
}
</style>
"""

# =========================================================================
# Preset career goals
# =========================================================================

PRESET_GOALS = [
    "Python Developer",
    "Data Scientist",
    "AI/ML Engineer",
    "Web Developer",
    "Cloud Engineer",
    "Cybersecurity Analyst",
    "Mobile App Developer",
    "DevOps Engineer",
]


# =========================================================================
# Session state
# =========================================================================

def _init_skill_state():
    """Initialise skill journey session state."""
    defaults = {
        "skill_phase": "auto",       # auto | setup | journey
        "skill_recommendation": None,
        "skill_project": {},         # {skill_id: project_text}
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


def _detect_phase() -> str:
    """Check if an active goal exists."""
    from services.skill_service import get_active_goal
    goal = get_active_goal()
    return "journey" if goal else "setup"


# =========================================================================
# PHASE: Setup
# =========================================================================

def _render_setup():
    """Render goal selection and roadmap generation form."""

    ai = _get_ai()
    ai_ok = ai.check_available()

    if not ai_ok:
        st.warning(
            "⚠️ **AI is unavailable.** Ollama is not running.\n\n"
            "Start it with `ollama serve` to generate roadmaps.",
            icon="🔌",
        )

    st.markdown("---")

    with st.container(border=True):
        st.markdown("#### 🎯 Choose Your Career Goal")

        # Preset buttons
        st.caption("Popular career paths:")
        cols = st.columns(4)
        selected_preset = None
        for i, goal in enumerate(PRESET_GOALS):
            with cols[i % 4]:
                if st.button(goal, key=f"preset_{i}", use_container_width=True):
                    selected_preset = goal

        st.markdown("")

        # Custom goal
        custom_goal = st.text_input(
            "Or enter a custom goal:",
            placeholder="e.g., Blockchain Developer, Game Designer...",
            key="custom_goal_input",
        )

        goal = selected_preset or custom_goal

        if goal:
            st.success(f"🎯 Selected: **{goal}**")

    st.markdown("")

    with st.container(border=True):
        st.markdown("#### 📊 Your Current Level")

        col1, col2 = st.columns(2)

        with col1:
            level = st.radio(
                "Select your level:",
                options=["🌱 Beginner", "📈 Intermediate", "🚀 Advanced"],
                index=0,
                key="skill_level",
            )
            # Clean the emoji prefix for the value
            level_clean = level.split(" ", 1)[1] if " " in level else level

        with col2:
            weekly_hours = st.select_slider(
                "Weekly study hours:",
                options=[2, 3, 5, 7, 10, 15, 20],
                value=5,
                format_func=lambda x: f"{x} hours/week",
                key="skill_weekly_hours",
            )

    st.markdown("")

    if st.button(
        "🚀 Generate My Roadmap",
        key="gen_roadmap",
        use_container_width=True,
        type="primary",
        disabled=not goal or not ai_ok,
    ):
        if not goal:
            st.error("Please select or enter a career goal.")
            return
        _generate_roadmap(goal, level_clean, weekly_hours)


def _generate_roadmap(goal: str, level: str, weekly_hours: float):
    """Generate roadmap and save to DB."""
    from services.skill_service import generate_roadmap, save_goal_to_db

    ai = _get_ai()

    try:
        with st.spinner(f"🤖 Creating your {goal} roadmap..."):
            skills = generate_roadmap(goal, level, weekly_hours, ai)

        if not skills:
            st.error("⚠️ Could not generate roadmap. Please try again.")
            return

        goal_id = save_goal_to_db(goal, level, weekly_hours, skills)

        if goal_id:
            st.session_state.skill_phase = "journey"
            st.session_state.skill_recommendation = None
            st.session_state.skill_project = {}
            st.rerun()
        else:
            st.error("⚠️ Could not save the roadmap. Please try again.")

    except ConnectionError as e:
        st.error(f"🔌 {e}")
    except ValueError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        st.error(f"⚠️ Roadmap generation failed: {e}")


# =========================================================================
# PHASE: Journey
# =========================================================================

def _render_journey():
    """Render the skill journey roadmap dashboard."""
    from services.skill_service import (
        get_active_goal, get_roadmap_progress, get_next_step,
        update_skill_status,
    )
    from services.study_service import get_assessment_topic_scores

    goal_data = get_active_goal()
    if not goal_data:
        st.session_state.skill_phase = "setup"
        st.rerun()
        return

    progress = get_roadmap_progress(goal_data["id"])
    next_step = get_next_step(goal_data)
    skills = goal_data.get("skills", [])
    assessment_scores = get_assessment_topic_scores()

    # --- Goal card ---
    st.markdown(
        f'<div class="goal-card">'
        f'<h3>🎯 {goal_data["goal"]}</h3>'
        f'<div class="meta">{goal_data["level"]} · {goal_data["weekly_hours"]} hrs/week</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --- Progress bar ---
    st.progress(
        progress["percentage"] / 100 if progress["percentage"] > 0 else 0.0,
        text=f"Skill Progress: {progress['completed']}/{progress['total']} completed ({progress['percentage']}%)"
    )

    # --- Stats row ---
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("✅ Completed", progress["completed"])
    with s2:
        st.metric("🔄 Learning", progress["learning"])
    with s3:
        st.metric("⬜ To Do", progress["not_started"])
    with s4:
        st.metric("⏱️ Est. Hours", f"{progress['done_hours']}/{progress['total_hours']}")

    # --- Next step ---
    if next_step:
        st.markdown(
            f'<div class="next-step-card">'
            f'🎯 <strong>Your Next Step:</strong> {next_step["name"]}'
            f'<br><small>{next_step.get("why_it_matters", "")}</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- Skill roadmap ---
    st.markdown("### 🗺️ Your Skill Roadmap")

    for skill in skills:
        _render_skill_card(skill, goal_data)

    # --- Action buttons ---
    st.markdown("---")
    act_cols = st.columns(3)

    with act_cols[0]:
        if st.button("🤖 Learn with AI Tutor", key="skill_to_tutor", use_container_width=True):
            st.session_state.student_section = "ai_tutor"
            if next_step:
                st.session_state.current_mode = "teach"
            st.rerun()

    with act_cols[1]:
        if st.button("📝 Take Assessment", key="skill_to_assess", use_container_width=True):
            st.session_state.student_section = "assessment"
            st.rerun()

    with act_cols[2]:
        if st.button("🆕 New Goal", key="new_goal", use_container_width=True):
            st.session_state.skill_phase = "setup"
            st.session_state.skill_recommendation = None
            st.session_state.skill_project = {}
            st.rerun()

    # --- AI Recommendation ---
    st.markdown("---")
    st.markdown("### 🧠 AI Recommendation")

    if st.session_state.skill_recommendation:
        st.markdown(
            f'<div class="rec-card">{st.session_state.skill_recommendation}</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.button("💡 Get Personalized Recommendation", key="gen_skill_rec", use_container_width=True):
            _generate_recommendation(goal_data, assessment_scores)

    # --- Assessment overlap warning ---
    if assessment_scores:
        _render_assessment_overlap(skills, assessment_scores)


def _render_skill_card(skill: dict, goal_data: dict):
    """Render a single skill card with status controls."""
    from services.skill_service import update_skill_status

    status = skill["status"]
    status_icons = {"not_started": "⬜", "learning": "🔄", "completed": "✅"}
    status_labels = {"not_started": "Not Started", "learning": "Learning", "completed": "Completed"}
    step_class = "done" if status == "completed" else ("active" if status == "learning" else "")

    with st.container(border=True):
        # Header row
        header_col, status_col = st.columns([4, 1.5])

        with header_col:
            st.markdown(
                f'<span class="step-number {step_class}">{skill["order"]}</span>'
                f'<strong>{skill["name"]}</strong> '
                f'<span style="color: #888; font-size: 0.85rem;">({skill.get("estimated_hours", 20)} hrs)</span>',
                unsafe_allow_html=True,
            )
            if skill.get("description"):
                st.caption(skill["description"])

        with status_col:
            new_status = st.selectbox(
                "Status",
                options=["not_started", "learning", "completed"],
                index=["not_started", "learning", "completed"].index(status),
                format_func=lambda s: f"{status_icons.get(s, '')} {status_labels.get(s, s)}",
                key=f"status_{skill['id']}",
                label_visibility="collapsed",
            )

            if new_status != status:
                update_skill_status(skill["id"], new_status)
                st.session_state.skill_recommendation = None
                st.rerun()

        # Expandable details
        with st.expander("📋 Details & Actions"):
            if skill.get("why_it_matters"):
                st.markdown(f"**Why it matters:** {skill['why_it_matters']}")
            if skill.get("practice_suggestion"):
                st.markdown(f"**Practice:** {skill['practice_suggestion']}")
            if skill.get("project_idea"):
                st.markdown(f"**Project idea:** {skill['project_idea']}")

            # Action buttons
            btn_cols = st.columns(3)

            with btn_cols[0]:
                if st.button(f"🤖 Learn", key=f"learn_{skill['id']}", use_container_width=True):
                    st.session_state.student_section = "ai_tutor"
                    st.session_state.current_mode = "teach"
                    st.session_state.chat_history = st.session_state.get("chat_history", [])
                    st.session_state.chat_history.append(
                        {"role": "user", "content": f"Teach me about {skill['name']} in detail"}
                    )
                    st.rerun()

            with btn_cols[1]:
                if st.button(f"📝 Practice", key=f"practice_{skill['id']}", use_container_width=True):
                    st.session_state.student_section = "assessment"
                    st.rerun()

            with btn_cols[2]:
                if st.button(f"🛠️ Project", key=f"project_{skill['id']}", use_container_width=True):
                    _generate_project(skill["id"], skill["name"], goal_data)


def _generate_project(skill_id: int, skill_name: str, goal_data: dict):
    """Generate and display a project challenge."""
    from services.skill_service import generate_project_challenge

    ai = _get_ai()

    # Check cache
    if skill_id in st.session_state.skill_project:
        return

    try:
        with st.spinner(f"🛠️ Generating project for {skill_name}..."):
            project = generate_project_challenge(
                ai, skill_name, goal_data["goal"], goal_data["level"]
            )
        st.session_state.skill_project[skill_id] = project
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Could not generate project: {e}")


def _generate_recommendation(goal_data: dict, assessment_scores: dict):
    """Generate and cache an AI recommendation."""
    from services.skill_service import generate_skill_recommendation

    ai = _get_ai()

    try:
        with st.spinner("🧠 Analyzing your progress..."):
            rec = generate_skill_recommendation(ai, goal_data, assessment_scores)
        st.session_state.skill_recommendation = rec
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Could not generate recommendation: {e}")


def _render_assessment_overlap(skills: list, assessment_scores: dict):
    """Show warnings if assessment scores indicate weakness in roadmap-related topics."""
    weak_matches = []
    assessment_topics = {t.lower(): data for t, data in assessment_scores.items()}

    for skill in skills:
        skill_lower = skill["name"].lower()
        for a_topic, a_data in assessment_topics.items():
            if (a_topic in skill_lower or skill_lower in a_topic) and a_data["percentage"] < 60:
                weak_matches.append((skill["name"], a_topic, a_data["percentage"]))

    if weak_matches:
        st.markdown("---")
        st.markdown("### ⚠️ Assessment Insights")
        for skill_name, topic, pct in weak_matches:
            st.warning(
                f"Your assessment shows **{topic}** at **{pct}%**. "
                f"Consider strengthening this before advancing past **{skill_name}**."
            )


# =========================================================================
# Main entry point
# =========================================================================

def show():
    """Render the Skill Journey section."""
    _init_skill_state()
    st.markdown(SKILL_CSS, unsafe_allow_html=True)

    # --- Header ---
    st.markdown(
        '<div class="hero-header" style="background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);">'
        '<h1>💻 Build Your Future</h1>'
        '<p>Turn your goal into an actionable learning journey</p></div>',
        unsafe_allow_html=True,
    )

    # Auto-detect phase
    phase = st.session_state.skill_phase
    if phase == "auto":
        phase = _detect_phase()
        st.session_state.skill_phase = phase

    # Show cached projects in journey phase
    if phase == "journey" and st.session_state.skill_project:
        for sid, project_text in st.session_state.skill_project.items():
            with st.expander(f"🛠️ Generated Project", expanded=True):
                st.markdown(project_text)

    # Route to current phase
    if phase == "setup":
        _render_setup()
    elif phase == "journey":
        _render_journey()
    else:
        _render_setup()
