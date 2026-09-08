"""
test_all_features.py - Full system verification suite for Smart Education.
"""
import sys
import os
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from services.classroom_service import (
    add_student, get_students, get_student_count,
    create_assignment, get_assignments, submit_assignment,
    get_class_average, get_topic_performance, get_students_needing_support
)
from services.pdf_service import extract_text_from_pdf, clean_text, chunk_text
from services.rag_service import RAGService
from services.ai_service import AIService
from pages.student import _init_session_state


class TestSmartEducation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_classroom_service(self):
        """Test student CRUD, assignments, and analytics."""
        s_id = add_student("Test User", "test_student@example.com")
        if not s_id:
            students = get_students()
            s_id = next((s["id"] for s in students if s["email"] == "test_student@example.com"), None)
        self.assertIsNotNone(s_id)
        count = get_student_count()
        self.assertGreater(count, 0)

        a_id = create_assignment("Test Assignment", "Solve problems", "Math", "2026-12-31")
        self.assertIsNotNone(a_id)

        sub_id = submit_assignment(a_id, s_id, "Test submission content")
        self.assertIsNotNone(sub_id)

        avg = get_class_average()
        self.assertIsInstance(avg, (int, float))

    def test_02_pdf_service(self):
        """Test PDF cleaning and chunking."""
        sample_text = "This is a sample document text.\n\n" * 20
        cleaned = clean_text(sample_text)
        self.assertIn("sample document text", cleaned)

        chunks = chunk_text(cleaned, chunk_size=100, overlap=20)
        self.assertGreater(len(chunks), 0)

    def test_03_rag_service(self):
        """Test RAG service instance and indexing structure."""
        rag = RAGService()
        self.assertFalse(rag.is_ready)
        self.assertEqual(len(rag.chunks), 0)

    def test_04_pdf_file_processing(self):
        """Test processing actual PDF file if present in Downloads."""
        pdf_path = os.path.join(os.path.expanduser("~"), "Downloads", "Coursera  UHV.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                text, pages = extract_text_from_pdf(f)
            self.assertGreater(pages, 0)
            self.assertGreater(len(text), 0)

    def test_05_student_session_state(self):
        """Test student dashboard session state initialization."""
        import streamlit as st
        _init_session_state()
        self.assertIn("student_section", st.session_state)
        self.assertIn("pdf_name", st.session_state)
        self.assertIn("pdf_chunks", st.session_state)
        self.assertIn("chat_history", st.session_state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
