"""
services/skill_service.py - Skill journey / career roadmap logic.

Handles:
- AI-powered roadmap generation
- Saving/loading goals and skills to/from DB
- Skill status tracking (not_started / learning / completed)
- Progress calculation
- Next-step recommendation
- Personalized AI recommendations using assessment data
- Project challenge generation
"""

import json
import re
from typing import List, Dict, Any, Optional

from services.prompt_templates import get_template, SYSTEM_SKILL


# =========================================================================
# Roadmap generation
# =========================================================================

def generate_roadmap(
    goal: str,
    level: str,
    weekly_hours: float,
    ai_service,
) -> List[Dict[str, Any]]:
    """Generate a structured skill roadmap using AI.

    Args:
        goal: Career goal (e.g. "Data Scientist").
        level: Beginner / Intermediate / Advanced.
        weekly_hours: Weekly study hours available.
        ai_service: AIService for LLM calls.

    Returns:
        List of skill dicts with order, name, description, etc.

    Raises:
        ValueError: If roadmap generation fails.
    """
    template = get_template("generate_roadmap")
    prompt = template.format(
        goal=goal,
        level=level,
        weekly_hours=weekly_hours,
    )

    response = ai_service.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=SYSTEM_SKILL,
    )

    skills = _parse_roadmap_response(response)

    if not skills:
        raise ValueError(
            "Could not generate a roadmap. Please try again or choose a different goal."
        )

    return skills


def _parse_roadmap_response(response: str) -> List[Dict[str, Any]]:
    """Parse LLM response into structured skill dicts."""
    try:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            skills = json.loads(json_match.group())
            if isinstance(skills, list) and len(skills) > 0:
                validated = [_validate_skill(s) for s in skills if _validate_skill(s)]
                if validated:
                    # Re-order sequentially
                    for i, s in enumerate(validated):
                        s["order"] = i + 1
                    return validated
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: try individual objects
    try:
        objects = re.findall(r'\{[^{}]+\}', response, re.DOTALL)
        validated = []
        for obj_str in objects:
            try:
                s = json.loads(obj_str)
                v = _validate_skill(s)
                if v:
                    validated.append(v)
            except (json.JSONDecodeError, TypeError):
                continue
        if validated:
            for i, s in enumerate(validated):
                s["order"] = i + 1
            return validated
    except Exception:
        pass

    return []


def _validate_skill(s: Any) -> Optional[Dict[str, Any]]:
    """Validate a skill dict."""
    if not isinstance(s, dict):
        return None

    name = str(s.get("name", "")).strip()
    if not name:
        return None

    return {
        "order": int(s.get("order", 0)),
        "name": name,
        "description": str(s.get("description", "")).strip(),
        "why_it_matters": str(s.get("why_it_matters", "")).strip(),
        "estimated_hours": int(s.get("estimated_hours", 20)) if isinstance(s.get("estimated_hours"), (int, float)) else 20,
        "practice_suggestion": str(s.get("practice_suggestion", "")).strip(),
        "project_idea": str(s.get("project_idea", "")).strip(),
    }


# =========================================================================
# Database persistence
# =========================================================================

def save_goal_to_db(
    goal: str,
    level: str,
    weekly_hours: float,
    skills: List[Dict[str, Any]],
) -> Optional[int]:
    """Save a skill goal and its roadmap to the database.

    Deactivates any previously active goal first.

    Returns:
        The goal ID, or None if saving failed.
    """
    try:
        from database import get_session
        from models import SkillGoal, SkillItem

        session = get_session()
        try:
            # Deactivate existing active goals
            session.query(SkillGoal).filter(
                SkillGoal.is_active == True
            ).update({"is_active": False})

            sg = SkillGoal(
                goal=goal,
                level=level,
                weekly_hours=weekly_hours,
                is_active=True,
            )
            session.add(sg)
            session.flush()

            for skill in skills:
                si = SkillItem(
                    goal_id=sg.id,
                    order=skill["order"],
                    name=skill["name"],
                    description=skill.get("description", ""),
                    why_it_matters=skill.get("why_it_matters", ""),
                    estimated_hours=skill.get("estimated_hours", 20),
                    practice_suggestion=skill.get("practice_suggestion", ""),
                    project_idea=skill.get("project_idea", ""),
                    status="not_started",
                )
                session.add(si)

            session.commit()
            return sg.id
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    except Exception:
        return None


def get_active_goal() -> Optional[Dict[str, Any]]:
    """Load the current active skill goal from the DB.

    Returns:
        Dict with goal metadata and skills, or None.
    """
    try:
        from database import get_session
        from models import SkillGoal, SkillItem

        session = get_session()
        try:
            sg = (
                session.query(SkillGoal)
                .filter(SkillGoal.is_active == True)
                .order_by(SkillGoal.created_at.desc())
                .first()
            )
            if not sg:
                return None

            items = (
                session.query(SkillItem)
                .filter(SkillItem.goal_id == sg.id)
                .order_by(SkillItem.order)
                .all()
            )

            skills = [
                {
                    "id": si.id,
                    "order": si.order,
                    "name": si.name,
                    "description": si.description,
                    "why_it_matters": si.why_it_matters,
                    "estimated_hours": si.estimated_hours,
                    "practice_suggestion": si.practice_suggestion,
                    "project_idea": si.project_idea,
                    "status": si.status,
                }
                for si in items
            ]

            return {
                "id": sg.id,
                "goal": sg.goal,
                "level": sg.level,
                "weekly_hours": sg.weekly_hours,
                "created_at": str(sg.created_at),
                "skills": skills,
            }
        finally:
            session.close()
    except Exception:
        return None


# =========================================================================
# Skill status management
# =========================================================================

def update_skill_status(skill_id: int, status: str) -> bool:
    """Update a skill's status.

    Args:
        skill_id: The SkillItem ID.
        status: "not_started", "learning", or "completed".

    Returns:
        True if successful.
    """
    if status not in ("not_started", "learning", "completed"):
        return False

    try:
        from database import get_session
        from models import SkillItem

        session = get_session()
        try:
            skill = session.query(SkillItem).filter(SkillItem.id == skill_id).first()
            if not skill:
                return False
            skill.status = status
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    except Exception:
        return False


# =========================================================================
# Progress calculation
# =========================================================================

def get_roadmap_progress(goal_id: int) -> Dict[str, Any]:
    """Calculate roadmap completion progress.

    Returns:
        Dict with total, completed, learning, not_started, percentage.
    """
    try:
        from database import get_session
        from models import SkillItem

        session = get_session()
        try:
            skills = (
                session.query(SkillItem)
                .filter(SkillItem.goal_id == goal_id)
                .all()
            )

            total = len(skills)
            completed = sum(1 for s in skills if s.status == "completed")
            learning = sum(1 for s in skills if s.status == "learning")
            not_started = sum(1 for s in skills if s.status == "not_started")
            pct = round(completed / total * 100, 1) if total > 0 else 0.0

            total_hours = sum(s.estimated_hours for s in skills)
            done_hours = sum(s.estimated_hours for s in skills if s.status == "completed")

            return {
                "total": total,
                "completed": completed,
                "learning": learning,
                "not_started": not_started,
                "percentage": pct,
                "total_hours": total_hours,
                "done_hours": done_hours,
            }
        finally:
            session.close()
    except Exception:
        return {"total": 0, "completed": 0, "learning": 0, "not_started": 0, "percentage": 0.0, "total_hours": 0, "done_hours": 0}


def get_next_step(goal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find the next skill to work on.

    Returns the first skill that is 'learning', or the first 'not_started' skill.
    """
    skills = goal_data.get("skills", [])

    # Priority 1: currently learning
    for s in skills:
        if s["status"] == "learning":
            return s

    # Priority 2: first not-started skill
    for s in skills:
        if s["status"] == "not_started":
            return s

    return None  # All completed


# =========================================================================
# AI Recommendations
# =========================================================================

def generate_skill_recommendation(
    ai_service,
    goal_data: Dict[str, Any],
    assessment_scores: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """Generate a personalized skill development recommendation.

    Args:
        ai_service: AIService instance.
        goal_data: Active goal dict with skills.
        assessment_scores: Topic scores from assessments.

    Returns:
        Recommendation string.
    """
    skills = goal_data.get("skills", [])
    progress = get_roadmap_progress(goal_data["id"])

    # Format skills status
    skills_status = "\n".join(
        f"- {s['name']}: {s['status'].replace('_', ' ')}"
        for s in skills
    )

    # Format assessment data
    if assessment_scores:
        assessment_data = "\n".join(
            f"- {topic}: {data['percentage']}%"
            for topic, data in sorted(assessment_scores.items(), key=lambda x: x[1]["percentage"])
        )
    else:
        assessment_data = "No assessment data available."

    progress_str = f"{progress['completed']}/{progress['total']} skills completed ({progress['percentage']}%)"

    template = get_template("skill_recommendation")
    prompt = template.format(
        goal=goal_data["goal"],
        level=goal_data["level"],
        progress=progress_str,
        skills_status=skills_status,
        assessment_data=assessment_data,
    )

    try:
        return ai_service.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SYSTEM_SKILL,
        )
    except Exception:
        # Fallback
        next_skill = get_next_step(goal_data)
        if next_skill:
            return (
                f"Your next recommended skill is **{next_skill['name']}**. "
                f"{next_skill.get('why_it_matters', 'This will help you progress toward your goal.')} "
                f"Aim to spend about {next_skill.get('estimated_hours', 20)} hours on this skill."
            )
        return "Great job! You've made excellent progress on your roadmap. Keep going!"


def generate_project_challenge(
    ai_service,
    skill_name: str,
    goal: str,
    level: str,
) -> str:
    """Generate a practical project challenge for a skill.

    Args:
        ai_service: AIService instance.
        skill_name: The skill to generate a project for.
        goal: Career goal context.
        level: Student's level.

    Returns:
        Project challenge markdown string.
    """
    template = get_template("project_challenge")
    prompt = template.format(
        skill_name=skill_name,
        goal=goal,
        level=level,
    )

    try:
        return ai_service.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SYSTEM_SKILL,
        )
    except Exception:
        return (
            f"🛠️ **Project: {skill_name} Practice**\n\n"
            f"Build a small project applying {skill_name} concepts. "
            f"Focus on practical implementation and test your understanding."
        )
