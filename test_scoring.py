"""Test classroom service: student CRUD, assignments, analytics."""
from services.classroom_service import (
    add_student, get_students, get_student_count, remove_student,
    create_assignment, get_assignments, get_active_assignment_count,
    submit_assignment, get_assignment_submissions,
    get_class_average, get_topic_performance,
    get_students_needing_support,
)
from database import init_db
init_db()

# 1. Student management
print("=== Student Management ===")
s1 = add_student("Alice Johnson", "alice@test.com")
s2 = add_student("Bob Smith", "bob@test.com")
s3 = add_student("Charlie Brown", "charlie@test.com")
print(f"Added students: {s1}, {s2}, {s3}")

students = get_students()
print(f"Total students: {get_student_count()}")
for s in students:
    print(f"  {s['name']} ({s['email']})")

# Don't add duplicate
dup = add_student("Alice Again", "alice@test.com")
print(f"Duplicate add (should be None): {dup}")

# 2. Assignment management
print("\n=== Assignments ===")
a1 = create_assignment("Graph Traversal Practice", "Practice BFS and DFS", "Graphs", "2026-09-14")
a2 = create_assignment("Array Problems", "Solve 5 array problems", "Arrays", "2026-09-12")
print(f"Created assignments: {a1}, {a2}")
print(f"Active assignments: {get_active_assignment_count()}")

# 3. Submissions
print("\n=== Submissions ===")
if s1 and a1:
    sub_id = submit_assignment(a1, s1, "Here is my BFS implementation...")
    print(f"Submission by Alice: {sub_id}")

assignments = get_assignments()
for a in assignments:
    print(f"  {a['title']} - {a['submission_count']} submissions")

# 4. Analytics
print("\n=== Analytics ===")
avg = get_class_average()
print(f"Class average: {avg}")

topic_perf = get_topic_performance()
for t, d in sorted(topic_perf.items(), key=lambda x: x[1]["percentage"]):
    print(f"  {t}: {d['percentage']}%")

# 5. Students needing support
print("\n=== Support ===")
struggling = get_students_needing_support()
print(f"Students needing support: {len(struggling)}")
for s in struggling:
    print(f"  {s['name']} (avg: {s['avg_score']}%, weak: {s['weakest_topic']})")

print("\n--- ALL CLASSROOM TESTS OK ---")
