"""
services/prompt_templates.py - Prompt templates for the AI Tutor.

Each template is a plain string with {placeholders} for dynamic content.
Templates are grouped by feature: RAG answering, learning modes, and
re-explanation styles.
"""

# =========================================================================
# SYSTEM PROMPTS
# =========================================================================

SYSTEM_BASE = (
    "You are an AI tutor inside the Smart Education platform. "
    "Your goal is to help students understand their study material clearly. "
    "Be encouraging, use simple language, and structure your answers with "
    "clear sections. Use markdown formatting."
)

SYSTEM_RAG = (
    SYSTEM_BASE + "\n\n"
    "CRITICAL RULES:\n"
    "1. PRIORITIZE the provided study material context above all else.\n"
    "2. If the context contains the answer, base your response on it.\n"
    "3. Do NOT invent facts, quotations, page numbers, or citations.\n"
    "4. If the answer is NOT found in the uploaded material, clearly tell the student:\n"
    '   "I couldn\'t find this information in your uploaded study material."\n'
    "   Then offer to explain using general knowledge if they want.\n"
    "5. If the student's question is ambiguous or unclear, ask a short clarification\n"
    "   question rather than guessing.\n"
    "6. Keep answers concise by default. Only provide more detail when asked.\n"
    "7. Maintain conversation context — refer back to earlier topics naturally.\n"
    "8. Structure your response with clear sections when appropriate.\n"
    "9. Never fabricate a source reference. Only say 'from your material' when the\n"
    "   retrieved context genuinely supports the answer."
)

# =========================================================================
# RAG ANSWER TEMPLATE
# =========================================================================

RAG_ANSWER = """Based on the student's uploaded study material, answer their question.

**Study Material Context:**
{context}

**Student's Question:**
{question}

RESPONSE RULES:
- Base your answer on the study material context provided above.
- If the context does NOT contain enough information, say clearly:
  "I couldn't find this in your uploaded study material."
  Then offer a brief general-knowledge explanation if appropriate.
- Do NOT invent citations, page numbers, or direct quotations.
- If the question is ambiguous, ask a short clarification question instead of guessing.
- Keep the answer concise unless the student asks for more detail.

When the context supports a full answer, structure your response using these sections:

💡 **Simple Explanation**
[Explain the concept clearly at the student's level — 2-4 sentences]

📌 **Key Points**
[2-5 important bullet points]

🌍 **Real-World Example** (when appropriate)
[An intuitive, relatable example]

🧪 **Technical Example** (when appropriate)
[A small code snippet, calculation, or worked example]

🧠 **Remember This**
[One concise takeaway sentence]

📚 **Source Context**
[If the answer came from the uploaded material, say: "This answer is based on your uploaded study material."
If it did NOT come from the material, say: "This was not found in your uploaded material — this is a general explanation."]
"""


# =========================================================================
# LEARNING MODE TEMPLATES
# =========================================================================

TEACH_ME = """The student wants to learn about this topic from their study material.

**Study Material Context:**
{context}

**Topic / Question:**
{question}

Explain this in a beginner-friendly way. Structure your response as:

💡 **Simple Explanation**
[Explain in plain, easy-to-understand language]

🌍 **Real-World Analogy**
[Connect it to something from everyday life]

💻 **Small Example**
[A short, concrete example]

🧠 **Key Takeaway**
[One sentence to remember]
"""

TEST_ME = """The student wants to be tested on their study material.

**Study Material Context:**
{context}

**Topic area:**
{question}

Generate ONE clear question to test the student's understanding of this topic.

Rules:
- Ask a specific, focused question
- Do NOT reveal the answer
- Do NOT give hints
- Make it test understanding, not just memorisation
- End with: "Take your time and type your answer below! 💪"

Format:
📝 **Question:**
[Your question here]
"""

EVALUATE_ANSWER = """The student answered a test question. Evaluate their response.

**Study Material Context:**
{context}

**Question that was asked:**
{question}

**Student's Answer:**
{student_answer}

Evaluate the student's answer:
1. Is it correct, partially correct, or incorrect?
2. What did they get right?
3. What could be improved?
4. Provide the correct/complete answer.

Format:
{"✅ **Correct!**" if correct, "🟡 **Partially Correct**" if partial, "❌ **Not Quite**" if wrong}

📝 **Your Answer Analysis:**
[What they got right/wrong]

✨ **Complete Answer:**
[The full correct answer]

💡 **Tip:**
[A helpful tip for remembering this]
"""

CHALLENGE_ME = """The student wants a challenging, application-based problem.

**Study Material Context:**
{context}

**Topic area:**
{question}

Create ONE challenging, application-based problem that requires the student
to APPLY the concepts (not just recall them).

Rules:
- Make it a real-world scenario or practical problem
- Require critical thinking
- Do NOT reveal the solution
- End with: "Think through this carefully and share your approach! 🚀"

Format:
🔴 **Challenge Problem:**
[Describe the scenario/problem]

🎯 **What you need to figure out:**
[Specific question to answer]
"""

# =========================================================================
# EXPLAIN DIFFERENTLY TEMPLATES
# =========================================================================

EXPLAIN_BEGINNER = """Re-explain the following concept as if the student is a complete beginner
with zero background knowledge. Use very simple words and short sentences.

**Previous explanation context:**
{context}

**Concept to re-explain:**
{question}

Format your answer as:
🧒 **Beginner-Friendly Explanation:**
[Use the simplest possible language]
"""

EXPLAIN_ANALOGY = """Re-explain the following concept using a vivid real-world analogy.

**Previous explanation context:**
{context}

**Concept to re-explain:**
{question}

Format your answer as:
🌍 **Real-World Analogy:**
[Create a clear, memorable analogy from everyday life]

🔗 **How It Connects:**
[Map the analogy back to the concept]
"""

EXPLAIN_ACADEMIC = """Re-explain the following concept in a formal, academic style
with precise terminology and thorough detail.

**Previous explanation context:**
{context}

**Concept to re-explain:**
{question}

Format your answer as:
📖 **Academic Explanation:**
[Formal, detailed explanation with proper terminology]

📚 **Key Definitions:**
[Important terms and their definitions]
"""

EXPLAIN_CODE = """Re-explain the following concept using a coding example.
Use Python if possible, or pseudocode if the concept isn't directly code-related.

**Previous explanation context:**
{context}

**Concept to re-explain:**
{question}

Format your answer as:
💻 **Code Example:**
```python
# Your code here
```

📝 **Code Walkthrough:**
[Line-by-line explanation of what the code does]
"""

EXPLAIN_QUICK = """Give an ultra-concise 30-second revision summary of this concept.
Maximum 3-4 sentences. Focus on what's essential for an exam.

**Previous explanation context:**
{context}

**Concept to re-explain:**
{question}

Format your answer as:
⚡ **30-Second Revision:**
[3-4 sentences max — just the essentials]
"""

# =========================================================================
# SUGGESTED QUESTIONS TEMPLATE
# =========================================================================

SUGGESTED_QUESTIONS = """Analyze the following study material and generate exactly 5 useful
questions a student might want to ask about it.

**Study Material (excerpts):**
{context}

Rules:
- Generate exactly 5 questions
- Make them diverse: mix conceptual, definitional, and application questions
- Keep each question concise (under 15 words)
- Format as a numbered list, one question per line
- Do NOT include any other text, just the 5 questions

Example format:
1. What is hashing and why is it used?
2. Explain the difference between stack and queue.
3. How does a linked list work in real life?
4. What are the key concepts in this chapter?
5. Compare linear search and binary search.
"""

# =========================================================================
# ASSESSMENT TEMPLATES (Step 3)
# =========================================================================

SYSTEM_ASSESSMENT = (
    "You are a quiz generator for the Smart Education platform. "
    "Generate high-quality multiple-choice questions based on the study material. "
    "Always output valid JSON. Be accurate and educational."
)

GENERATE_MCQ = """Generate {num_questions} multiple-choice questions from the study material below.

**Study Material Context:**
{context}

**Topic focus:** {topic}
**Difficulty:** {difficulty}

Rules:
- Each question must have exactly 4 options: A, B, C, D
- Exactly one option must be correct
- Include a brief explanation for the correct answer
- Tag each question with a specific sub-topic
- Match the requested difficulty level
- Questions must be based on the provided study material
- Do NOT repeat questions

You MUST respond with ONLY a valid JSON array. No other text before or after.
Each object in the array must have these exact keys:
"question", "A", "B", "C", "D", "correct", "topic", "difficulty", "explanation"

The "correct" field must be exactly one of: "A", "B", "C", "D"

Example format:
[
  {{
    "question": "What is the time complexity of binary search?",
    "A": "O(n)",
    "B": "O(log n)",
    "C": "O(n^2)",
    "D": "O(1)",
    "correct": "B",
    "topic": "Searching Algorithms",
    "difficulty": "Medium",
    "explanation": "Binary search divides the search space in half each step, giving O(log n)."
  }}
]
"""

EXPLAIN_WRONG_ANSWER = """The student answered a quiz question incorrectly. Give a concise explanation.

**Question:** {question}
**Student's Answer:** {student_answer}
**Correct Answer:** {correct_answer}
**Correct Option Text:** {correct_text}

**Study Material Context:**
{context}

Provide a SHORT explanation (3-5 sentences max):

💡 **Why?**
[Explain why the correct answer is right and why the student's choice was wrong]

🧠 **Remember This:**
[One-sentence takeaway]
"""

ADAPTIVE_TEACH = """The student scored poorly on the topic "{topic}" in their assessment.
Teach them this topic in a concise, beginner-friendly way.

**Study Material Context:**
{context}

Provide:

💡 **Quick Explanation**
[2-3 sentences explaining the core concept]

📌 **Key Points**
[3-4 bullet points]

🌍 **Simple Example**
[One concrete example]

🧠 **Remember This**
[One-sentence takeaway]
"""

GENERATE_PRACTICE_MCQ = """Generate {num_questions} practice multiple-choice questions focused
specifically on the topic "{topic}" to help the student improve their weak area.

**Study Material Context:**
{context}

**Difficulty:** {difficulty}

Rules:
- Focus ONLY on the topic "{topic}"
- Make questions that test understanding, not just memorisation
- Each question must have exactly 4 options: A, B, C, D
- Include a brief explanation for the correct answer

You MUST respond with ONLY a valid JSON array. No other text.
Each object must have keys: "question", "A", "B", "C", "D", "correct", "topic", "difficulty", "explanation"
The "correct" field must be exactly one of: "A", "B", "C", "D"
"""

# =========================================================================
# STUDY WORKFLOW TEMPLATES (Step 4)
# =========================================================================

SYSTEM_STUDY = (
    "You are a study planner for the Smart Education platform. "
    "Create realistic, achievable study plans based on the student's material, "
    "assessment performance, and available time. Always output valid JSON when asked. "
    "Be practical and encouraging."
)

GENERATE_STUDY_PLAN = """Create a personalized daily study plan for the student.

**Study Material Topics:**
{topics}

**Weak Topics (from assessment):**
{weak_topics}

**Exam Date:** {exam_date}
**Days Until Exam:** {days_until_exam}
**Daily Study Time:** {daily_hours} hours
**Study Preference:** {preference}

Rules:
- Create a plan for {num_days} days (minimum 3, maximum 14)
- Prioritize weak topics — schedule them MORE frequently and EARLIER
- Each day should have 2-4 tasks that fit within {daily_hours} hours
- Task types: "learn" (read/understand), "practice" (solve problems), "review" (revise)
- Strong topics need only light review
- Include variety — mix learning and practice each day
- Be realistic — do not overload any single day
- Final 1-2 days should be revision/review

You MUST respond with ONLY a valid JSON array. No other text.
Each object must represent one day with these keys:
"day" (integer), "theme" (string — main focus), "tasks" (array of task objects)

Each task object must have:
"topic" (string), "type" (string: learn/practice/review), "duration" (integer: minutes), "description" (string: short action item)

Example:
[
  {{
    "day": 1,
    "theme": "Graph Fundamentals",
    "tasks": [
      {{"topic": "Graphs", "type": "learn", "duration": 45, "description": "Study BFS and DFS traversal"}},
      {{"topic": "Graphs", "type": "practice", "duration": 30, "description": "Solve 3 graph traversal problems"}}
    ]
  }}
]
"""

EXTRACT_TOPICS = """Analyze the following study material excerpts and identify the main topics covered.

**Study Material:**
{context}

Rules:
- List between 3 and 10 distinct topics
- Keep topic names short (2-4 words each)
- Focus on academic/conceptual topics
- Do NOT list page numbers or chapter numbers

Respond with ONLY a JSON array of topic strings. No other text.
Example: ["Arrays", "Linked Lists", "Binary Trees", "Graph Algorithms", "Sorting"]
"""

LEARNING_INSIGHT = """Generate a personalized study recommendation for the student.

**Assessment Performance:**
{assessment_data}

**Current Study Plan Status:**
{plan_status}

**Study Material Topics:**
{topics}

Rules:
- Be specific — mention actual topic names and scores
- Give ONE actionable recommendation (2-3 sentences max)
- Be encouraging but honest
- Reference the student's actual performance data

Format:
[Your recommendation here — no headers, just the text]
"""

# =========================================================================
# SKILL JOURNEY TEMPLATES (Step 5)
# =========================================================================

SYSTEM_SKILL = (
    "You are a career and skill development advisor for the Smart Education platform. "
    "Create structured, actionable skill roadmaps and recommendations. "
    "Always output valid JSON when asked. Be practical and motivating."
)

GENERATE_ROADMAP = """Create a structured skill roadmap for a student working toward this career goal.

**Career Goal:** {goal}
**Current Level:** {level}
**Weekly Study Hours:** {weekly_hours}

Rules:
- Create 6-10 skills in logical learning order (prerequisites first)
- Adjust depth and complexity based on the student's level
- Each skill should be a concrete, learnable unit
- Include practical applications and project ideas
- Estimate realistic learning hours for the student's level
- For Beginner: start with fundamentals, more hand-holding
- For Intermediate: skip basics, focus on applied skills
- For Advanced: focus on specialisation and real-world projects

You MUST respond with ONLY a valid JSON array. No other text.
Each object must have these keys:
"order" (integer 1-N), "name" (string: short skill name), "description" (string: what to learn),
"why_it_matters" (string: 1 sentence), "estimated_hours" (integer),
"practice_suggestion" (string: how to practice), "project_idea" (string: small project)

Example:
[
  {{
    "order": 1,
    "name": "Python Fundamentals",
    "description": "Variables, data types, control flow, functions, and OOP basics",
    "why_it_matters": "Python is the foundation for data science and ML workflows",
    "estimated_hours": 40,
    "practice_suggestion": "Solve 20 coding problems on basic Python concepts",
    "project_idea": "Build a command-line expense tracker with file storage"
  }}
]
"""

SKILL_RECOMMENDATION = """Generate a personalized skill development recommendation.

**Career Goal:** {goal}
**Current Level:** {level}
**Roadmap Progress:** {progress}
**Skills Status:** {skills_status}

**Assessment Performance (if available):**
{assessment_data}

Rules:
- Be specific — mention actual skill names and assessment scores
- Give ONE actionable recommendation (2-3 sentences max)
- If assessment data shows weakness in a foundation skill, recommend strengthening it first
- Be encouraging but practical
- Reference the student's actual data

Format:
[Your recommendation — no headers, just the text]
"""

PROJECT_CHALLENGE = """Generate a practical project challenge for a student learning this skill.

**Skill:** {skill_name}
**Career Goal:** {goal}
**Student Level:** {level}

Rules:
- Keep the project achievable in 2-4 hours
- Make it relevant to the career goal
- Include clear requirements (3-5 bullet points)
- Suggest one bonus/stretch feature
- Be specific — not vague

Format:
🛠️ **Project: [Project Name]**

**What to build:**
[1-2 sentence description]

**Requirements:**
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

⭐ **Bonus:**
[Stretch feature]

💡 **Tip:**
[One helpful hint]
"""

# =========================================================================
# CLASSROOM INTELLIGENCE TEMPLATES (Step 6)
# =========================================================================

SYSTEM_CLASSROOM = (
    "You are a classroom analytics assistant for the Smart Education platform. "
    "Analyze real student performance data and provide actionable insights for teachers. "
    "Be specific, use actual data from the input, and suggest practical classroom actions. "
    "Never invent statistics that are not in the data."
)

CLASSROOM_INSIGHT = """Analyze the following classroom data and provide actionable insights for the teacher.

**Class Summary:**
{class_summary}

**Topic-wise Performance:**
{topic_performance}

**Assignment Status:**
{assignment_status}

**Students Needing Support:**
{struggling_students}

Rules:
- Use ONLY the data provided. Do NOT invent statistics.
- Identify the weakest topic(s) across the class.
- Mention specific students needing support (by name) if data is available.
- Give ONE specific recommended action the teacher should take.
- Keep the total response under 200 words.
- Be encouraging but honest about areas that need improvement.

Format your response as:

📊 **Class Analysis**
[2-3 sentences about overall class performance]

⚠️ **Key Finding**
[The most important insight from the data]

🎯 **Recommended Action**
[One specific, practical action the teacher should take next]
"""

# =========================================================================
# TEMPLATE REGISTRY — easy lookup by name
# =========================================================================

TEMPLATES = {
    "rag_answer": RAG_ANSWER,
    "teach_me": TEACH_ME,
    "test_me": TEST_ME,
    "evaluate_answer": EVALUATE_ANSWER,
    "challenge_me": CHALLENGE_ME,
    "explain_beginner": EXPLAIN_BEGINNER,
    "explain_analogy": EXPLAIN_ANALOGY,
    "explain_academic": EXPLAIN_ACADEMIC,
    "explain_code": EXPLAIN_CODE,
    "explain_quick": EXPLAIN_QUICK,
    "suggested_questions": SUGGESTED_QUESTIONS,
    "generate_mcq": GENERATE_MCQ,
    "explain_wrong_answer": EXPLAIN_WRONG_ANSWER,
    "adaptive_teach": ADAPTIVE_TEACH,
    "generate_practice_mcq": GENERATE_PRACTICE_MCQ,
    "generate_study_plan": GENERATE_STUDY_PLAN,
    "extract_topics": EXTRACT_TOPICS,
    "learning_insight": LEARNING_INSIGHT,
    "generate_roadmap": GENERATE_ROADMAP,
    "skill_recommendation": SKILL_RECOMMENDATION,
    "project_challenge": PROJECT_CHALLENGE,
    "classroom_insight": CLASSROOM_INSIGHT,
}


def get_template(name: str) -> str:
    """Get a prompt template by name.

    Args:
        name: Template key (e.g. 'rag_answer', 'teach_me').

    Returns:
        The template string with {placeholders}.

    Raises:
        KeyError: If the template name doesn't exist.
    """
    if name not in TEMPLATES:
        raise KeyError(
            f"Unknown template '{name}'. "
            f"Available: {list(TEMPLATES.keys())}"
        )
    return TEMPLATES[name]
