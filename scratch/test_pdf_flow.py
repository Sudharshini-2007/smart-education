"""
scratch/test_pdf_flow.py - Verify PDF processing and RAG pipeline with sample PDF.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_service import extract_text_from_pdf, clean_text, chunk_text
from services.rag_service import RAGService
from services.ai_service import AIService

def test_pdf():
    pdf_path = r"C:\Users\jayashree\Downloads\Coursera  UHV.pdf"
    if not os.path.exists(pdf_path):
        print(f"ERROR: {pdf_path} not found")
        return

    print(f"Reading {pdf_path}...")
    with open(pdf_path, "rb") as f:
        text, num_pages = extract_text_from_pdf(f)
    
    cleaned = clean_text(text)
    chunks = chunk_text(cleaned)
    print(f"Extracted {num_pages} pages, {len(chunks)} chunks.")
    print("Sample chunk:", chunks[0][:150] if chunks else "NO CHUNKS")

    ai = AIService()
    print(f"AI Service available: {ai.check_available()}")
    if ai.check_available():
        rag = RAGService()
        print("Building index...")
        rag.build_index(chunks[:10], ai)  # test first 10 chunks
        print(f"RAG ready: {rag.is_ready}")
        results = rag.search("What is UHV?", ai, top_k=2)
        print("RAG search results count:", len(results))
        for r in results:
            print(" - Chunk sample:", r[:100])
    else:
        print("Ollama not running (skipping live embedding search test).")

if __name__ == "__main__":
    test_pdf()
