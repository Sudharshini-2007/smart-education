"""
services/study_service.py - Study plan generation, tracking, and adaptation.

Handles:
- Fetching assessment topic scores from the DB
- Extracting topics from uploaded study material
- AI-powered study plan generation (weighted by weak topics)
- Saving/loading plans and tasks to/from DB
- Task completion tracking
- Study streak calculation
- Adaptive rescheduling for incomplete tasks
- AI learning insight generation
"""

import json
import re
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional

from services.prompt_templates import get_template, SYSTEM_STUDY


# =========================================================================
# Assessment data retrieval
# =========================================================================

def get_assessment_topic_scores() -> Dict[str, Dict[str, Any]]:
    """Query the latest assessment's topic-wise scores from the DB.

    Returns:
        Dict mapping topic -> {correct, total, percentage}.
        Empty dict if no assessments exist.
    """
    try:
        from database import get_session
        from models import Assessment, AssessmentQuestion

        session = get_session()
        try:
            latest = (
                session.query(Assessment)
                .order_by(Assessment.created_at.desc())
                .first()
            )
            if not latest:
                return {}

            questions = (
                session.query(AssessmentQuestion)
                .filter(AssessmentQuestion.assessment_id == latest.id)
                .all()
            )

            topic_stats: Dict[str, Dict[str, int]] = {}
            for q in questions:
                topic = q.topic or "General"
                if topic not in topic_stats:
                    topic_stats[topic] = {"correct": 0, "total": 0}
                topic_stats[topic]["total"] += 1
                if q.is_correct:
                    topic_stats[topic]["correct"] += 1

            result = {}
            for topic, stats in topic_stats.items():
                pct = round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0.0
                result[topic] = {
                    "correct": stats["correct"],
                    "total": stats["total"],
                    "percentage": pct,
                }
            return result
        finally:
            session.close()
    except Exception:
        return {}


def get_assessment_average() -> Optional[float]:
    """Get the average percentage across all assessments."""
    try:
        from database import get_session
        from models import Assessment

        session = get_session()
        try:
            assessments = session.query(Assessment).all()
            if not assessments:
                return None
            avg = sum(a.percentage for a in assessments) / len(assessments)
            return round(avg, 1)
        finally:
            session.close()
    except Exception:
        return None


# =========================================================================
# Topic extraction from study material
# =========================================================================

def extract_topics_from_chunks(chunks: List[str], ai_service) -> List[str]:
    """Use AI to identify key topics from uploaded study material.

    Args:
        chunks: Text chunks from the uploaded PDF.
        ai_service: AIService for LLM calls.

    Returns:
        List of topic strings.
    """
    if not chunks:
        return []

    # Use a sample of chunks for efficiency
    sample = chunks[:8]
    context = "\n\n---\n\n".join(sample)

    template = get_template("extract_topics")
    prompt = template.format(context=context)

    try:
        response = ai_service.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SYSTEM_STUDY,
        )

        # Parse JSON array
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            topics = json.loads(json_match.group())
            if isinstance(topics, list):
                return [str(t).strip() for t in topics if str(t).strip()]
    except Exception:
        pass

    # Fallback: return generic topics
    return ["General Topics"]


# =========================================================================
# Study plan generation
# =========================================================================

def generate_study_plan(
    topics: List[str],
    weak_topics: Dict[str, float],
    exam_date_str: str,
    daily_hours: float,
    preference: str,
    rag_service,
    ai_service,
) -> List[Dict[str, Any]]:
    """Generate a multi-day study plan using AI.

    Args:
        topics: List of topic names from study material.
        weak_topics: Dict mapping topic -> percentage from assessment.
        exam_date_str: Exam date as YYYY-MM-DD.
        daily_hours: Available study hours per day.
        preference: "Learn concepts" / "Practice questions" / "Balanced".
        rag_service: RAGService for context.
        ai_service: AIService for LLM calls.

    Returns:
        List of day dicts with tasks.

    Raises:
        ValueError: If plan generation fails.
    """
    # Calculate days until exam
    try:
        exam_dt = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        today = date.today()
        days_left = (exam_dt - today).days
        if days_left < 1:
            days_left = 7  # default if exam date is past
    except (ValueError, TypeError):
        days_left = 7

    num_days = min(max(days_left, 3), 14)

    # Format weak topics info
    if weak_topics:
        weak_info = "\n".join(
            f"- {topic}: {pct}% (needs {'urgent' if pct < 40 else 'more'} practice)"
            for topic, pct in sorted(weak_topics.items(), key=lambda x: x[1])
        )
    else:
        weak_info = "No assessment data yet — treat all topics equally."

    topics_str = ", ".join(topics) if topics else "General"

    template = get_template("generate_study_plan")
    prompt = template.format(
        topics=topics_str,
        weak_topics=weak_info,
        exam_date=exam_date_str,
        days_until_exam=days_left,
        daily_hours=daily_hours,
        preference=preference,
        num_days=num_days,
    )

    response = ai_service.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=SYSTEM_STUDY,
    )

    plan = _parse_plan_response(response)

    if not plan:
        # Fallback: generate a simple plan programmatically
        plan = _generate_fallback_plan(topics, weak_topics, num_days, daily_hours)

    return plan


def _parse_plan_response(response: str) -> List[Dict[str, Any]]:
    """Parse LLM response into structured plan data."""
    try:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            days = json.loads(json_match.group())
            if isinstance(days, list) and len(days) > 0:
                validated = []
                for day in days:
                    v = _validate_day(day)
                    if v:
                        validated.append(v)
                return validated if validated else []
    except (json.JSONDecodeError, TypeError):
        pass

    # Try extracting individual JSON objects
    try:
        objects = re.findall(r'\{[^{}]*"tasks"\s*:\s*\[.*?\]\s*\}', response, re.DOTALL)
        validated = []
        for obj_str in objects:
            try:
                day = json.loads(obj_str)
                v = _validate_day(day)
                if v:
                    validated.append(v)
            except (json.JSONDecodeError, TypeError):
                continue
        return validated
    except Exception:
        pass

    return []


def _validate_day(day: Any) -> Optional[Dict[str, Any]]:
    """Validate a day object from the plan."""
    if not isinstance(day, dict):
        return None

    day_num = day.get("day")
    if not isinstance(day_num, (int, float)):
        return None

    theme = str(day.get("theme", "Study Session")).strip()
    tasks = day.get("tasks", [])

    if not isinstance(tasks, list) or not tasks:
        return None

    valid_tasks = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        topic = str(t.get("topic", "")).strip()
        task_type = str(t.get("type", "learn")).strip().lower()
        duration = t.get("duration", 30)
        desc = str(t.get("description", "")).strip()

        if not topic:
            continue
        if task_type not in ("learn", "practice", "review"):
            task_type = "learn"
        if not isinstance(duration, (int, float)) or duration < 5:
            duration = 30

        valid_tasks.append({
            "topic": topic,
            "type": task_type,
            "duration": int(duration),
            "description": desc or f"{task_type.capitalize()} {topic}",
        })

    if not valid_tasks:
        return None

    return {
        "day": int(day_num),
        "theme": theme,
        "tasks": valid_tasks,
    }


def _generate_fallback_plan(
    topics: List[str],
    weak_topics: Dict[str, float],
    num_days: int,
    daily_hours: float,
) -> List[Dict[str, Any]]:
    """Generate a simple study plan without AI (fallback)."""
    if not topics:
        topics = ["General"]

    daily_minutes = int(daily_hours * 60)
    plan = []

    # Sort topics: weak first, then others
    sorted_topics = sorted(
        topics,
        key=lambda t: weak_topics.get(t, 50.0)
    )

    for day_idx in range(num_days):
        topic_idx = day_idx % len(sorted_topics)
        topic = sorted_topics[topic_idx]
        is_weak = weak_topics.get(topic, 50.0) < 60

        tasks = []
        remaining = daily_minutes

        # Learn task
        learn_time = min(remaining, 45 if is_weak else 30)
        tasks.append({
            "topic": topic,
            "type": "learn",
            "duration": learn_time,
            "description": f"Study {topic} concepts",
        })
        remaining -= learn_time

        # Practice task
        if remaining >= 20:
            practice_time = min(remaining, 30)
            tasks.append({
                "topic": topic,
                "type": "practice",
                "duration": practice_time,
                "description": f"Solve {topic} practice problems",
            })
            remaining -= practice_time

        # Review task (if time remains)
        if remaining >= 15 and len(sorted_topics) > 1:
            review_topic = sorted_topics[(topic_idx + 1) % len(sorted_topics)]
            tasks.append({
                "topic": review_topic,
                "type": "review",
                "duration": min(remaining, 20),
                "description": f"Quick review of {review_topic}",
            })

        plan.append({
            "day": day_idx + 1,
            "theme": f"{'Deep Dive' if is_weak else 'Study'}: {topic}",
            "tasks": tasks,
        })

    return plan


# =========================================================================
# Database persistence
# =========================================================================

def save_plan_to_db(
    plan_data: List[Dict[str, Any]],
    exam_date: str,
    daily_hours: float,
    preference: str,
    pdf_name: Optional[str] = None,
) -> Optional[int]:
    """Save a study plan and its tasks to the database.

    Deactivates any previously active plan first.

    Returns:
        The plan ID, or None if saving failed.
    """
    try:
        from database import get_session
        from models import StudyPlan, StudyTask

        session = get_session()
        try:
            # Deactivate existing active plans
            session.query(StudyPlan).filter(
                StudyPlan.is_active == True
            ).update({"is_active": False})

            plan = StudyPlan(
                exam_date=exam_date,
                daily_hours=daily_hours,
                preference=preference,
                pdf_name=pdf_name,
                num_days=len(plan_data),
                is_active=True,
            )
            session.add(plan)
            session.flush()

            for day in plan_data:
                for task in day.get("tasks", []):
                    st = StudyTask(
                        plan_id=plan.id,
                        day_number=day["day"],
                        topic=task["topic"],
                        task_type=task["type"],
                        duration_minutes=task["duration"],
                        description=task.get("description", ""),
                    )
                    session.add(st)

            session.commit()
            return plan.id
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    except Exception:
        return None


def get_active_plan() -> Optional[Dict[str, Any]]:
    """Load the current active study plan from the DB.

    Returns:
        Dict with plan metadata and tasks grouped by day, or None.
    """
    try:
        from database import get_session
        from models import StudyPlan, StudyTask

        session = get_session()
        try:
            plan = (
                session.query(StudyPlan)
                .filter(StudyPlan.is_active == True)
                .order_by(StudyPlan.created_at.desc())
                .first()
            )
            if not plan:
                return None

            tasks = (
                session.query(StudyTask)
                .filter(StudyTask.plan_id == plan.id)
                .order_by(StudyTask.day_number, StudyTask.id)
                .all()
            )

            # Group tasks by day
            days: Dict[int, Dict[str, Any]] = {}
            for t in tasks:
                if t.day_number not in days:
                    days[t.day_number] = {"day": t.day_number, "tasks": []}
                days[t.day_number]["tasks"].append({
                    "id": t.id,
                    "topic": t.topic,
                    "type": t.task_type,
                    "duration": t.duration_minutes,
                    "description": t.description,
                    "is_completed": t.is_completed,
                })

            return {
                "id": plan.id,
                "exam_date": plan.exam_date,
                "daily_hours": plan.daily_hours,
                "preference": plan.preference,
                "pdf_name": plan.pdf_name,
                "num_days": plan.num_days,
                "created_at": str(plan.created_at),
                "days": dict(sorted(days.items())),
            }
        finally:
            session.close()
    except Exception:
        return None


def get_today_tasks(plan_id: int) -> List[Dict[str, Any]]:
    """Get the current day's tasks (based on plan creation date).

    Calculates which day the student is on relative to the plan start.
    """
    try:
        from database import get_session
        from models import StudyPlan, StudyTask

        session = get_session()
        try:
            plan = session.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
            if not plan:
                return []

            # Calculate current day number
            plan_start = plan.created_at.date() if plan.created_at else date.today()
            current_day = (date.today() - plan_start).days + 1
            current_day = max(1, min(current_day, plan.num_days))

            tasks = (
                session.query(StudyTask)
                .filter(StudyTask.plan_id == plan_id, StudyTask.day_number == current_day)
                .order_by(StudyTask.id)
                .all()
            )

            return [
                {
                    "id": t.id,
                    "topic": t.topic,
                    "type": t.task_type,
                    "duration": t.duration_minutes,
                    "description": t.description,
                    "is_completed": t.is_completed,
                    "day_number": t.day_number,
                }
                for t in tasks
            ], current_day
        finally:
            session.close()
    except Exception:
        return [], 1


# =========================================================================
# Task completion
# =========================================================================

def mark_task_complete(task_id: int) -> bool:
    """Mark a study task as completed and update daily progress."""
    try:
        from database import get_session
        from models import StudyTask, StudyProgress

        session = get_session()
        try:
            task = session.query(StudyTask).filter(StudyTask.id == task_id).first()
            if not task:
                return False

            task.is_completed = True
            task.completed_at = datetime.now(timezone.utc)

            # Update daily progress
            today_str = date.today().isoformat()
            progress = (
                session.query(StudyProgress)
                .filter(StudyProgress.date == today_str)
                .first()
            )

            if progress:
                progress.tasks_completed += 1
                progress.study_minutes += task.duration_minutes
            else:
                # Count today's total tasks
                total_today = (
                    session.query(StudyTask)
                    .filter(
                        StudyTask.plan_id == task.plan_id,
                        StudyTask.day_number == task.day_number,
                    )
                    .count()
                )
                progress = StudyProgress(
                    date=today_str,
                    tasks_completed=1,
                    tasks_total=total_today,
                    study_minutes=task.duration_minutes,
                )
                session.add(progress)

            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    except Exception:
        return False


def mark_task_incomplete(task_id: int) -> bool:
    """Unmark a study task (toggle back to incomplete)."""
    try:
        from database import get_session
        from models import StudyTask, StudyProgress

        session = get_session()
        try:
            task = session.query(StudyTask).filter(StudyTask.id == task_id).first()
            if not task:
                return False

            task.is_completed = False
            task.completed_at = None

            # Update daily progress
            today_str = date.today().isoformat()
            progress = (
                session.query(StudyProgress)
                .filter(StudyProgress.date == today_str)
                .first()
            )
            if progress and progress.tasks_completed > 0:
                progress.tasks_completed -= 1
                progress.study_minutes = max(0, progress.study_minutes - task.duration_minutes)

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
# Study streak
# =========================================================================

def get_study_streak() -> int:
    """Calculate the number of consecutive days with study activity."""
    try:
        from database import get_session
        from models import StudyProgress

        session = get_session()
        try:
            records = (
                session.query(StudyProgress)
                .filter(StudyProgress.tasks_completed > 0)
                .order_by(StudyProgress.date.desc())
                .all()
            )

            if not records:
                return 0

            streak = 0
            check_date = date.today()

            for record in records:
                try:
                    record_date = datetime.strptime(record.date, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    continue

                if record_date == check_date:
                    streak += 1
                    check_date -= timedelta(days=1)
                elif record_date == check_date - timedelta(days=1):
                    # Allow checking yesterday if today has no record yet
                    if streak == 0:
                        streak += 1
                        check_date = record_date - timedelta(days=1)
                    else:
                        break
                else:
                    break

            return streak
        finally:
            session.close()
    except Exception:
        return 0


# =========================================================================
# Adaptive rescheduling
# =========================================================================

def reschedule_incomplete(plan_id: int) -> int:
    """Move incomplete tasks from past days to the next available day.

    Returns:
        Number of tasks rescheduled.
    """
    try:
        from database import get_session
        from models import StudyPlan, StudyTask

        session = get_session()
        try:
            plan = session.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
            if not plan:
                return 0

            plan_start = plan.created_at.date() if plan.created_at else date.today()
            current_day = max(1, (date.today() - plan_start).days + 1)

            # Find incomplete tasks from past days (not today)
            incomplete = (
                session.query(StudyTask)
                .filter(
                    StudyTask.plan_id == plan_id,
                    StudyTask.is_completed == False,
                    StudyTask.day_number < current_day,
                )
                .all()
            )

            if not incomplete:
                return 0

            # Move them to current day
            count = 0
            for task in incomplete:
                task.day_number = current_day
                count += 1

            session.commit()
            return count
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()
    except Exception:
        return 0


# =========================================================================
# AI Learning Insight
# =========================================================================

def generate_learning_insight(
    rag_service,
    ai_service,
    topic_scores: Dict[str, Dict[str, Any]],
    plan_info: Optional[Dict[str, Any]] = None,
    material_topics: Optional[List[str]] = None,
) -> str:
    """Generate a personalized AI study recommendation.

    Args:
        rag_service: RAGService instance.
        ai_service: AIService instance.
        topic_scores: Assessment topic scores.
        plan_info: Current plan status dict.
        material_topics: List of topics from study material.

    Returns:
        A recommendation string.
    """
    # Format assessment data
    if topic_scores:
        assessment_data = "\n".join(
            f"- {topic}: {data['percentage']}% ({data['correct']}/{data['total']})"
            for topic, data in sorted(topic_scores.items(), key=lambda x: x[1]["percentage"])
        )
    else:
        assessment_data = "No assessment data available yet."

    # Format plan status
    if plan_info:
        plan_status = f"Active plan with {plan_info['num_days']} days."
        total_tasks = sum(len(d["tasks"]) for d in plan_info.get("days", {}).values())
        done_tasks = sum(
            1 for d in plan_info.get("days", {}).values()
            for t in d["tasks"] if t.get("is_completed")
        )
        plan_status += f" Progress: {done_tasks}/{total_tasks} tasks completed."
    else:
        plan_status = "No active study plan."

    topics_str = ", ".join(material_topics) if material_topics else "Unknown"

    template = get_template("learning_insight")
    prompt = template.format(
        assessment_data=assessment_data,
        plan_status=plan_status,
        topics=topics_str,
    )

    try:
        return ai_service.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SYSTEM_STUDY,
        )
    except Exception:
        # Fallback: generate simple insight from data
        if topic_scores:
            weakest = min(topic_scores.items(), key=lambda x: x[1]["percentage"])
            return (
                f"Your assessment shows that **{weakest[0]}** is your weakest area "
                f"at {weakest[1]['percentage']}%. Consider dedicating extra time to "
                f"this topic before your next assessment."
            )
        return "Upload study material and take an assessment to get personalized insights."


# =========================================================================
# Progress summary
# =========================================================================

def get_progress_summary() -> Dict[str, Any]:
    """Get overall study progress stats."""
    plan = get_active_plan()
    streak = get_study_streak()
    avg_score = get_assessment_average()
    topic_scores = get_assessment_topic_scores()

    # Count completed topics (all tasks done for that topic)
    topics_completed = 0
    topics_total = 0
    priority_topic = None

    if plan:
        topic_completion: Dict[str, Dict[str, int]] = {}
        for day_data in plan.get("days", {}).values():
            for task in day_data.get("tasks", []):
                t = task["topic"]
                if t not in topic_completion:
                    topic_completion[t] = {"total": 0, "done": 0}
                topic_completion[t]["total"] += 1
                if task.get("is_completed"):
                    topic_completion[t]["done"] += 1

        topics_total = len(topic_completion)
        topics_completed = sum(
            1 for tc in topic_completion.values()
            if tc["total"] > 0 and tc["done"] == tc["total"]
        )

    # Find priority topic from assessment
    if topic_scores:
        weakest = min(topic_scores.items(), key=lambda x: x[1]["percentage"])
        priority_topic = weakest[0]

    return {
        "topics_completed": topics_completed,
        "topics_total": topics_total,
        "assessment_avg": avg_score,
        "streak": streak,
        "priority_topic": priority_topic,
        "has_plan": plan is not None,
    }
