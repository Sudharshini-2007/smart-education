"""
services/quiz_service.py - Quiz generation, scoring, and analysis.

Handles:
- MCQ generation via RAG + LLM
- Deterministic scoring (pure Python, no LLM)
- Weak topic detection
- AI explanations for wrong answers
- Adaptive practice question generation
"""

import json
import re
from typing import List, Dict, Optional, Any

from services.prompt_templates import get_template, SYSTEM_ASSESSMENT


# =========================================================================
# MCQ Generation
# =========================================================================

def generate_quiz(
    rag_service,
    ai_service,
    topic: str = "General",
    num_questions: int = 5,
    difficulty: str = "Medium",
) -> List[Dict[str, str]]:
    """Generate MCQ questions from uploaded study material.

    Args:
        rag_service: The RAGService with a built FAISS index.
        ai_service: The AIService for LLM calls.
        topic: Topic focus (or "General" for broad).
        num_questions: Number of questions to generate.
        difficulty: Easy / Medium / Hard.

    Returns:
        List of question dicts, each with keys:
        question, A, B, C, D, correct, topic, difficulty, explanation

    Raises:
        ValueError: If questions can't be generated.
        ConnectionError: If Ollama is unreachable.
    """
    if not rag_service.is_ready:
        raise ValueError("No study material loaded. Please upload a PDF first.")

    # Retrieve broad context for question generation
    context_chunks = rag_service.search(topic, ai_service, top_k=5)
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else ""

    if not context.strip():
        raise ValueError("Could not find relevant content in the study material.")

    template = get_template("generate_mcq")
    prompt = template.format(
        context=context,
        topic=topic,
        num_questions=num_questions,
        difficulty=difficulty,
    )

    response = ai_service.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=SYSTEM_ASSESSMENT,
    )

    questions = _parse_mcq_response(response)

    if not questions:
        raise ValueError(
            "Could not generate quiz questions. "
            "Try a different topic or upload more detailed material."
        )

    # Ensure we have the right count (LLM might give more or fewer)
    return questions[:num_questions]


def _parse_mcq_response(response: str) -> List[Dict[str, str]]:
    """Parse LLM response into structured MCQ dicts.

    Tries JSON parsing first, falls back to regex extraction.
    """
    # --- Attempt 1: Direct JSON parse ---
    try:
        # Find JSON array in response (might have markdown code fences)
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group())
            if isinstance(questions, list) and len(questions) > 0:
                validated = [_validate_question(q) for q in questions if _validate_question(q)]
                if validated:
                    return validated
    except (json.JSONDecodeError, TypeError):
        pass

    # --- Attempt 2: Try parsing line by line for individual JSON objects ---
    try:
        objects = re.findall(r'\{[^{}]+\}', response, re.DOTALL)
        questions = []
        for obj_str in objects:
            try:
                q = json.loads(obj_str)
                validated = _validate_question(q)
                if validated:
                    questions.append(validated)
            except (json.JSONDecodeError, TypeError):
                continue
        if questions:
            return questions
    except Exception:
        pass

    return []


def _validate_question(q: Any) -> Optional[Dict[str, str]]:
    """Validate that a question dict has all required fields."""
    if not isinstance(q, dict):
        return None

    required = ["question", "A", "B", "C", "D", "correct"]
    for key in required:
        if key not in q or not str(q[key]).strip():
            return None

    # Normalize the correct answer
    correct = str(q["correct"]).strip().upper()
    if correct not in ("A", "B", "C", "D"):
        return None

    return {
        "question": str(q["question"]).strip(),
        "A": str(q["A"]).strip(),
        "B": str(q["B"]).strip(),
        "C": str(q["C"]).strip(),
        "D": str(q["D"]).strip(),
        "correct": correct,
        "topic": str(q.get("topic", "General")).strip(),
        "difficulty": str(q.get("difficulty", "Medium")).strip(),
        "explanation": str(q.get("explanation", "")).strip(),
    }


# =========================================================================
# Deterministic Scoring
# =========================================================================

def score_quiz(
    questions: List[Dict[str, str]],
    answers: Dict[int, str],
) -> Dict[str, Any]:
    """Score a completed quiz using pure Python logic.

    Args:
        questions: The list of question dicts (from generate_quiz).
        answers: Dict mapping question index (0-based) to answer letter (A/B/C/D).

    Returns:
        Dict with: total, correct, incorrect, percentage,
        per_question (list of result dicts), topic_scores, difficulty_scores.
    """
    total = len(questions)
    correct = 0
    incorrect = 0
    per_question = []
    topic_stats: Dict[str, Dict[str, int]] = {}
    difficulty_stats: Dict[str, Dict[str, int]] = {}

    for i, q in enumerate(questions):
        student_answer = answers.get(i, "")
        correct_answer = q["correct"]
        is_correct = student_answer.upper() == correct_answer.upper()

        if is_correct:
            correct += 1
        else:
            incorrect += 1

        per_question.append({
            "index": i,
            "question": q["question"],
            "A": q["A"],
            "B": q["B"],
            "C": q["C"],
            "D": q["D"],
            "correct_answer": correct_answer,
            "student_answer": student_answer,
            "is_correct": is_correct,
            "topic": q.get("topic", "General"),
            "difficulty": q.get("difficulty", "Medium"),
            "explanation": q.get("explanation", ""),
        })

        # Track topic stats
        topic = q.get("topic", "General")
        if topic not in topic_stats:
            topic_stats[topic] = {"total": 0, "correct": 0}
        topic_stats[topic]["total"] += 1
        if is_correct:
            topic_stats[topic]["correct"] += 1

        # Track difficulty stats
        diff = q.get("difficulty", "Medium")
        if diff not in difficulty_stats:
            difficulty_stats[diff] = {"total": 0, "correct": 0}
        difficulty_stats[diff]["total"] += 1
        if is_correct:
            difficulty_stats[diff]["correct"] += 1

    percentage = round((correct / total * 100), 1) if total > 0 else 0.0

    # Calculate topic percentages
    topic_scores = {}
    for topic, stats in topic_stats.items():
        pct = round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0.0
        topic_scores[topic] = {
            "correct": stats["correct"],
            "total": stats["total"],
            "percentage": pct,
        }

    # Calculate difficulty percentages
    difficulty_scores = {}
    for diff, stats in difficulty_stats.items():
        pct = round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0.0
        difficulty_scores[diff] = {
            "correct": stats["correct"],
            "total": stats["total"],
            "percentage": pct,
        }

    return {
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "percentage": percentage,
        "per_question": per_question,
        "topic_scores": topic_scores,
        "difficulty_scores": difficulty_scores,
    }


# =========================================================================
# Weak Topic Detection
# =========================================================================

def detect_weak_topics(
    topic_scores: Dict[str, Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Classify topics into strong, attention, and weak categories.

    Args:
        topic_scores: Dict from score_quiz output.

    Returns:
        Dict with keys: strong (≥70%), attention (40-69%), weak (<40%).
        Each value is a list of {topic, percentage, correct, total}.
    """
    strong = []
    attention = []
    weak = []

    for topic, data in topic_scores.items():
        entry = {
            "topic": topic,
            "percentage": data["percentage"],
            "correct": data["correct"],
            "total": data["total"],
        }
        if data["percentage"] >= 70:
            strong.append(entry)
        elif data["percentage"] >= 40:
            attention.append(entry)
        else:
            weak.append(entry)

    # Sort each category by percentage
    strong.sort(key=lambda x: x["percentage"], reverse=True)
    attention.sort(key=lambda x: x["percentage"])
    weak.sort(key=lambda x: x["percentage"])

    return {"strong": strong, "attention": attention, "weak": weak}


# =========================================================================
# AI Explanation for Wrong Answers
# =========================================================================

def generate_explanation(
    rag_service,
    ai_service,
    question_result: Dict[str, Any],
) -> str:
    """Generate an AI explanation for an incorrect answer.

    Args:
        rag_service: RAGService for context retrieval.
        ai_service: AIService for LLM calls.
        question_result: A per_question result dict from score_quiz.

    Returns:
        A markdown-formatted explanation string.
    """
    try:
        context_chunks = rag_service.search(
            question_result["question"], ai_service, top_k=2
        )
        context = "\n\n".join(context_chunks) if context_chunks else "No context available."

        student_letter = question_result["student_answer"]
        correct_letter = question_result["correct_answer"]

        template = get_template("explain_wrong_answer")
        prompt = template.format(
            question=question_result["question"],
            student_answer=f"{student_letter}. {question_result.get(student_letter, 'N/A')}",
            correct_answer=correct_letter,
            correct_text=question_result.get(correct_letter, ""),
            context=context,
        )

        return ai_service.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=SYSTEM_ASSESSMENT,
        )
    except Exception as e:
        return f"💡 The correct answer is **{question_result['correct_answer']}**. {question_result.get('explanation', '')}"


# =========================================================================
# Adaptive Practice
# =========================================================================

def generate_adaptive_lesson(
    rag_service,
    ai_service,
    topic: str,
) -> str:
    """Generate a short teaching lesson for a weak topic.

    Args:
        rag_service: RAGService for context retrieval.
        ai_service: AIService for LLM calls.
        topic: The weak topic to teach.

    Returns:
        A markdown-formatted lesson string.
    """
    context_chunks = rag_service.search(topic, ai_service, top_k=3)
    context = "\n\n".join(context_chunks) if context_chunks else "No context available."

    template = get_template("adaptive_teach")
    prompt = template.format(topic=topic, context=context)

    return ai_service.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=SYSTEM_ASSESSMENT,
    )


def generate_practice_questions(
    rag_service,
    ai_service,
    topic: str,
    num_questions: int = 3,
    difficulty: str = "Medium",
) -> List[Dict[str, str]]:
    """Generate practice MCQs focused on a specific weak topic.

    Args:
        rag_service: RAGService for context retrieval.
        ai_service: AIService for LLM calls.
        topic: The topic to focus on.
        num_questions: Number of practice questions.
        difficulty: Difficulty level.

    Returns:
        List of question dicts.
    """
    context_chunks = rag_service.search(topic, ai_service, top_k=4)
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else ""

    template = get_template("generate_practice_mcq")
    prompt = template.format(
        context=context,
        topic=topic,
        num_questions=num_questions,
        difficulty=difficulty,
    )

    response = ai_service.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=SYSTEM_ASSESSMENT,
    )

    questions = _parse_mcq_response(response)
    return questions[:num_questions]


# =========================================================================
# Database persistence
# =========================================================================

def save_assessment_to_db(
    quiz_result: Dict[str, Any],
    topic: str,
    difficulty: str,
    pdf_name: Optional[str] = None,
) -> Optional[int]:
    """Save an assessment and its questions to the database.

    Args:
        quiz_result: The result dict from score_quiz.
        topic: The assessment topic.
        difficulty: The assessment difficulty.
        pdf_name: Name of the source PDF.

    Returns:
        The assessment ID, or None if saving failed.
    """
    try:
        from database import get_session
        from models import Assessment, AssessmentQuestion

        session = get_session()
        try:
            assessment = Assessment(
                topic=topic,
                difficulty=difficulty,
                num_questions=quiz_result["total"],
                score=quiz_result["correct"],
                percentage=quiz_result["percentage"],
                pdf_name=pdf_name,
            )
            session.add(assessment)
            session.flush()  # get the ID

            for pq in quiz_result["per_question"]:
                aq = AssessmentQuestion(
                    assessment_id=assessment.id,
                    question_text=pq["question"],
                    option_a=pq["A"],
                    option_b=pq["B"],
                    option_c=pq["C"],
                    option_d=pq["D"],
                    correct_answer=pq["correct_answer"],
                    student_answer=pq["student_answer"] or None,
                    topic=pq.get("topic"),
                    difficulty=pq.get("difficulty"),
                    explanation=pq.get("explanation"),
                    is_correct=pq["is_correct"],
                )
                session.add(aq)

            session.commit()
            return assessment.id
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    except Exception:
        return None
