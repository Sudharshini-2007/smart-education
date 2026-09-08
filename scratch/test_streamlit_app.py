"""
scratch/test_streamlit_app.py - Test student dashboard PDF upload using Streamlit AppTest.
"""
import sys
import os
from pathlib import Path

# Force UTF-8 output encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def test_app():
    from streamlit.testing.v1 import AppTest

    app_path = str(ROOT_DIR / "app.py")
    print(f"Initializing AppTest for {app_path}...")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()

    print("Initial page run completed.")

    # Click Student button
    print("Clicking Student button...")
    for btn in at.button:
        print(f"Button label: '{btn.label}'")
        if "Student" in btn.label:
            btn.click()
            break
    
    at.run()
    print("\n--- After selecting student role ---")
    print("Session state role:", at.session_state["role"] if "role" in at.session_state else None)
    print("Session state pdf_name:", at.session_state["pdf_name"] if "pdf_name" in at.session_state else None)
    print("Session state student_section:", at.session_state["student_section"] if "student_section" in at.session_state else None)

    # Test uploading a file
    pdf_path = os.path.join(os.path.expanduser("~"), "Downloads", "Coursera  UHV.pdf")
    if os.path.exists(pdf_path) and len(at.file_uploader) > 0:
        print(f"\nUploading {pdf_path} to file_uploader...")
        uploader = at.file_uploader[0]
        uploader.upload_from_file(pdf_path)
        at.run()

        print("\n--- After upload run ---")
        print("pdf_name in session_state:", at.session_state["pdf_name"] if "pdf_name" in at.session_state else None)
        print("pdf_chunks count:", len(at.session_state["pdf_chunks"]) if "pdf_chunks" in at.session_state else 0)
        print("pdf_upload_msg:", at.session_state["pdf_upload_msg"] if "pdf_upload_msg" in at.session_state else None)
        print("chat_history:", at.session_state["chat_history"] if "chat_history" in at.session_state else None)
        
        # Check markdown elements
        markdown_texts = [m.value for m in at.markdown]
        print("\nMarkdown snippets:")
        for m in markdown_texts:
            if any(k in m for k in ["Upload a PDF", "Coursera", "AI Tutor", "Suggested Questions", "Learning Modes", "No Study Material"]):
                print(" -> ", repr(m[:120]))

if __name__ == "__main__":
    test_app()
