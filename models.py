"""
models.py - SQLAlchemy models for Smart Education.

Step 1 defines a minimal User model. Step 3 adds Assessment models.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """A user of the platform (student or teacher)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # "student" or "teacher"
    bio = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}')>"


# ---------------------------------------------------------------
# Assessment models (Step 3)
# ---------------------------------------------------------------

class Assessment(Base):
    """A quiz/assessment taken by a student."""

    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)       # Easy / Medium / Hard
    num_questions = Column(Integer, nullable=False)
    score = Column(Integer, default=0)                    # correct count
    percentage = Column(Float, default=0.0)
    pdf_name = Column(String(300), nullable=True)         # source material
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    questions = relationship(
        "AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Assessment(id={self.id}, topic='{self.topic}', "
            f"score={self.score}/{self.num_questions})>"
        )


class AssessmentQuestion(Base):
    """A single question within an assessment."""

    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)    # A / B / C / D
    student_answer = Column(String(1), nullable=True)     # A / B / C / D or None
    topic = Column(String(200), nullable=True)
    difficulty = Column(String(20), nullable=True)
    explanation = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)

    assessment = relationship("Assessment", back_populates="questions")

    def __repr__(self):
        return (
            f"<AssessmentQuestion(id={self.id}, "
            f"correct={self.correct_answer}, student={self.student_answer})>"
        )



# ---------------------------------------------------------------
# Study Workflow models (Step 4)
# ---------------------------------------------------------------

class StudyPlan(Base):
    """A personalized study plan."""

    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_date = Column(String(20), nullable=True)          # YYYY-MM-DD
    daily_hours = Column(Float, default=2.0)
    preference = Column(String(30), default="Balanced")    # Learn / Practice / Balanced
    pdf_name = Column(String(300), nullable=True)
    num_days = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    tasks = relationship(
        "StudyTask", back_populates="plan", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<StudyPlan(id={self.id}, days={self.num_days}, active={self.is_active})>"


class StudyTask(Base):
    """A single task within a study plan."""

    __tablename__ = "study_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    day_number = Column(Integer, nullable=False)            # 1-based
    topic = Column(String(200), nullable=False)
    task_type = Column(String(20), nullable=False)          # learn / practice / review
    duration_minutes = Column(Integer, default=30)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    plan = relationship("StudyPlan", back_populates="tasks")

    def __repr__(self):
        return (
            f"<StudyTask(id={self.id}, day={self.day_number}, "
            f"topic='{self.topic}', done={self.is_completed})>"
        )


class StudyProgress(Base):
    """Daily study activity record for streak tracking."""

    __tablename__ = "study_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, unique=True)  # YYYY-MM-DD
    tasks_completed = Column(Integer, default=0)
    tasks_total = Column(Integer, default=0)
    study_minutes = Column(Integer, default=0)

    def __repr__(self):
        return (
            f"<StudyProgress(date='{self.date}', "
            f"done={self.tasks_completed}/{self.tasks_total})>"
        )


# ---------------------------------------------------------------
# Skill Journey models (Step 5)
# ---------------------------------------------------------------

class SkillGoal(Base):
    """A career/skill development goal."""

    __tablename__ = "skill_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal = Column(String(200), nullable=False)
    level = Column(String(20), nullable=False)              # Beginner / Intermediate / Advanced
    weekly_hours = Column(Float, default=5.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    skills = relationship(
        "SkillItem", back_populates="goal_ref", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SkillGoal(id={self.id}, goal='{self.goal}', level='{self.level}')>"


class SkillItem(Base):
    """A single skill within a career roadmap."""

    __tablename__ = "skill_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("skill_goals.id"), nullable=False)
    order = Column(Integer, nullable=False)                 # 1-based sequence
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    estimated_hours = Column(Integer, default=20)
    practice_suggestion = Column(Text, nullable=True)
    project_idea = Column(Text, nullable=True)
    status = Column(String(20), default="not_started")      # not_started / learning / completed

    goal_ref = relationship("SkillGoal", back_populates="skills")

    def __repr__(self):
        return f"<SkillItem(id={self.id}, name='{self.name}', status='{self.status}')>"


# ---------------------------------------------------------------
# Classroom models (Step 6)
# ---------------------------------------------------------------

class Assignment(Base):
    """A teacher-created assignment."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(200), nullable=True)
    deadline = Column(String(20), nullable=True)            # YYYY-MM-DD
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    submissions = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Assignment(id={self.id}, title='{self.title}')>"


class Submission(Base):
    """A student's submission for an assignment."""

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=True)
    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    assignment = relationship("Assignment", back_populates="submissions")

    def __repr__(self):
        return f"<Submission(id={self.id}, assignment={self.assignment_id}, student={self.student_id})>"


# ---------------------------------------------------------------
# Future models (later steps):
# ---------------------------------------------------------------
# class Notification(Base): ...
