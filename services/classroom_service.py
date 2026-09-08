"""
services/classroom_service.py - Teacher classroom intelligence logic.

Handles:
- Student management (add/list/remove)
- Assignment CRUD
- Submission management
- Class performance analytics (from real assessment data)
- AI classroom insight generation
- Identifying students needing support
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from services.prompt_templates import get_template, SYSTEM_CLASSROOM


# =========================================================================
# Student management
# =========================================================================

def add_student(name: str, email: str) -> Optional[int]:
    """Add a student to the database."""
    try:
        from database import get_session
        from models import User
        session = get_session()
        try:
            existing = session.query(User).filter(User.email == email).first()
            if existing:
                return None  # email already taken
            student = User(name=name, email=email, role="student")
            session.add(student)
            session.commit()
            return student.id
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    except Exception:
        return None


def get_students() -> List[Dict[str, Any]]:
    """Get all students."""
    try:
        from database import get_session
        from models import User
        session = get_session()
        try:
            students = (
                session.query(User)
                .filter(User.role == "student")
                .order_by(User.name)
                .all()
            )
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "email": s.email,
                    "created_at": str(s.created_at) if s.created_at else "",
                }
                for s in students
            ]
        finally:
            session.close()
    except Exception:
        return []


def remove_student(student_id: int) -> bool:
    """Remove a student by ID."""
    try:
        from database import get_session
        from models import User
        session = get_session()
        try:
            student = session.query(User).filter(
                User.id == student_id, User.role == "student"
            ).first()
            if not student:
                return False
            session.delete(student)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    except Exception:
        return False


def get_student_count() -> int:
    """Count total students."""
    try:
        from database import get_session
        from models import User
        session = get_session()
        try:
            return session.query(User).filter(User.role == "student").count()
        finally:
            session.close()
    except Exception:
        return 0


# =========================================================================
# Assignment management
# =========================================================================

def create_assignment(title: str, description: str, topic: str, deadline: str) -> Optional[int]:
    """Create a new assignment."""
    try:
        from database import get_session
        from models import Assignment
        session = get_session()
        try:
            a = Assignment(
                title=title,
                description=description,
                topic=topic,
                deadline=deadline,
                is_active=True,
            )
            session.add(a)
            session.commit()
            return a.id
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    except Exception:
        return None


def get_assignments(active_only: bool = False) -> List[Dict[str, Any]]:
    """Get all assignments."""
    try:
        from database import get_session
        from models import Assignment, Submission
        session = get_session()
        try:
            q = session.query(Assignment).order_by(Assignment.created_at.desc())
            if active_only:
                q = q.filter(Assignment.is_active == True)
            assignments = q.all()

            result = []
            for a in assignments:
                sub_count = session.query(Submission).filter(
                    Submission.assignment_id == a.id
                ).count()
                result.append({
                    "id": a.id,
                    "title": a.title,
                    "description": a.description,
                    "topic": a.topic,
                    "deadline": a.deadline,
                    "is_active": a.is_active,
                    "created_at": str(a.created_at) if a.created_at else "",
                    "submission_count": sub_count,
                })
            return result
        finally:
            session.close()
    except Exception:
        return []


def get_active_assignment_count() -> int:
    """Count active assignments."""
    try:
        from database import get_session
        from models import Assignment
        session = get_session()
        try:
            return session.query(Assignment).filter(Assignment.is_active == True).count()
        finally:
            session.close()
    except Exception:
        return 0


def submit_assignment(assignment_id: int, student_id: int, content: str) -> Optional[int]:
    """Submit an assignment as a student."""
    try:
        from database import get_session
        from models import Submission
        session = get_session()
        try:
            # Check for duplicate submission
            existing = session.query(Submission).filter(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
            ).first()
            if existing:
                existing.content = content
                existing.submitted_at = datetime.now(timezone.utc)
                session.commit()
                return existing.id

            sub = Submission(
                assignment_id=assignment_id,
                student_id=student_id,
                content=content,
            )
            session.add(sub)
            session.commit()
            return sub.id
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    except Exception:
        return None


def get_assignment_submissions(assignment_id: int) -> List[Dict[str, Any]]:
    """Get all submissions for an assignment."""
    try:
        from database import get_session
        from models import Submission, User
        session = get_session()
        try:
            subs = (
                session.query(Submission, User.name)
                .join(User, Submission.student_id == User.id)
                .filter(Submission.assignment_id == assignment_id)
                .order_by(Submission.submitted_at.desc())
                .all()
            )
            return [
                {
                    "id": sub.id,
                    "student_name": name,
                    "student_id": sub.student_id,
                    "content": sub.content,
                    "grade": sub.grade,
                    "feedback": sub.feedback,
                    "submitted_at": str(sub.submitted_at) if sub.submitted_at else "",
                }
                for sub, name in subs
            ]
        finally:
            session.close()
    except Exception:
        return []


# =========================================================================
# Class performance analytics
# =========================================================================

def get_class_average() -> Optional[float]:
    """Get the average assessment score across all assessments."""
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


def get_topic_performance() -> Dict[str, Dict[str, Any]]:
    """Get topic-wise performance from all assessment questions."""
    try:
        from database import get_session
        from models import AssessmentQuestion
        session = get_session()
        try:
            questions = session.query(AssessmentQuestion).all()
            if not questions:
                return {}

            topics: Dict[str, Dict[str, int]] = {}
            for q in questions:
                t = q.topic or "General"
                if t not in topics:
                    topics[t] = {"correct": 0, "total": 0}
                topics[t]["total"] += 1
                if q.is_correct:
                    topics[t]["correct"] += 1

            result = {}
            for topic, data in topics.items():
                pct = round(data["correct"] / data["total"] * 100, 1) if data["total"] > 0 else 0.0
                result[topic] = {
                    "correct": data["correct"],
                    "total": data["total"],
                    "percentage": pct,
                }
            return result
        finally:
            session.close()
    except Exception:
        return {}


def get_students_needing_support() -> List[Dict[str, Any]]:
    """Identify students who may need additional support.

    Uses assessment data and student records to find those with
    low averages or weak topics.
    """
    # Since assessments currently aren't linked to a specific User,
    # we analyse the global assessment data and correlate with student list
    students = get_students()
    topic_perf = get_topic_performance()
    class_avg = get_class_average()

    if not students:
        return []

    # Find weak topics
    weak_topics = []
    for topic, data in topic_perf.items():
        if data["percentage"] < 60:
            weak_topics.append({"topic": topic, "percentage": data["percentage"]})

    # Sort weakest first
    weak_topics.sort(key=lambda x: x["percentage"])

    # Build attention list: students + their weakest area
    result = []
    weakest_topic = weak_topics[0]["topic"] if weak_topics else None
    weakest_pct = weak_topics[0]["percentage"] if weak_topics else None

    for student in students:
        entry = {
            "id": student["id"],
            "name": student["name"],
            "avg_score": class_avg,
            "weakest_topic": weakest_topic,
            "weakest_pct": weakest_pct,
        }
        # Flag for support if class average is below 60 or weak topics exist
        if (class_avg is not None and class_avg < 60) or weak_topics:
            result.append(entry)

    return result


# =========================================================================
# AI Classroom Insight
# =========================================================================

def generate_classroom_insight(ai_service) -> str:
    """Generate an AI-powered classroom insight from real stored data.

    Uses actual assessment data, assignment data, and student data.
    """
    students = get_students()
    class_avg = get_class_average()
    topic_perf = get_topic_performance()
    assignments = get_assignments()
    struggling = get_students_needing_support()

    # Check if we have enough data
    if not topic_perf and not assignments and not students:
        return (
            "📊 **Not enough class data yet.**\n\n"
            "Add students, create assignments, and have students take assessments "
            "to generate meaningful classroom insights."
        )

    # Format class summary
    class_summary = f"{len(students)} students enrolled."
    if class_avg is not None:
        class_summary += f" Average class score: {class_avg}%."
    else:
        class_summary += " No assessment data yet."

    # Format topic performance
    if topic_perf:
        topic_lines = []
        for topic, data in sorted(topic_perf.items(), key=lambda x: x[1]["percentage"]):
            icon = "🟢" if data["percentage"] >= 70 else ("🟠" if data["percentage"] >= 40 else "🔴")
            topic_lines.append(f"{icon} {topic}: {data['percentage']}% ({data['correct']}/{data['total']} correct)")
        topic_str = "\n".join(topic_lines)
    else:
        topic_str = "No topic performance data available."

    # Format assignment status
    if assignments:
        active = sum(1 for a in assignments if a["is_active"])
        total_subs = sum(a["submission_count"] for a in assignments)
        assignment_str = f"{len(assignments)} assignments created ({active} active). {total_subs} total submissions."
    else:
        assignment_str = "No assignments created yet."

    # Format struggling students
    if struggling:
        struggling_lines = [
            f"- {s['name']} (class avg: {s['avg_score']}%, weakest: {s['weakest_topic']} at {s['weakest_pct']}%)"
            for s in struggling[:5]
        ]
        struggling_str = "\n".join(struggling_lines)
    else:
        struggling_str = "No students flagged for additional support."

    template = get_template("classroom_insight")
    prompt = template.format(
        class_summary=class_summary,
        topic_performance=topic_str,
        assignment_status=assignment_str,
        struggling_students=struggling_str,
    )

    try:
        return ai_service.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SYSTEM_CLASSROOM,
        )
    except Exception:
        # Fallback: generate a simple data-driven insight without AI
        return _generate_fallback_insight(class_avg, topic_perf, assignments, struggling)


def _generate_fallback_insight(class_avg, topic_perf, assignments, struggling):
    """Generate a simple insight without AI (fallback)."""
    lines = ["📊 **Class Analysis**\n"]

    if class_avg is not None:
        if class_avg >= 70:
            lines.append(f"The class is performing well with an average of {class_avg}%.")
        elif class_avg >= 50:
            lines.append(f"The class average is {class_avg}%. There is room for improvement.")
        else:
            lines.append(f"The class average is {class_avg}%. Students need significant additional support.")

    if topic_perf:
        weakest = min(topic_perf.items(), key=lambda x: x[1]["percentage"])
        lines.append(f"\n⚠️ **Key Finding**\n")
        lines.append(
            f"**{weakest[0]}** is the weakest topic at {weakest[1]['percentage']}%. "
            f"Consider dedicating extra class time to this area."
        )

    if struggling:
        lines.append(f"\n🎯 **Recommended Action**\n")
        lines.append(
            f"Focus on strengthening the weakest topics through targeted practice. "
            f"{len(struggling)} student(s) may need individual attention."
        )

    return "\n".join(lines) if len(lines) > 1 else "Not enough data to generate insights."
