"""
services/pdf_service.py - PDF text extraction and chunking.

Handles:
- Reading uploaded PDF files
- Extracting text from each page
- Cleaning extracted text
- Splitting text into overlapping chunks for RAG embedding
"""

import re
from typing import List, Tuple


def extract_text_from_pdf(uploaded_file) -> Tuple[str, int]:
    """Extract text from an uploaded PDF file.

    Args:
        uploaded_file: A Streamlit UploadedFile object (or any file-like with .read()).

    Returns:
        A tuple of (extracted_text, number_of_pages).

    Raises:
        ValueError: If the PDF is empty or text extraction fails.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "pypdf is not installed. Run: pip install pypdf"
        )

    try:
        reader = PdfReader(uploaded_file)
        num_pages = len(reader.pages)

        if num_pages == 0:
            raise ValueError("The PDF file has no pages.")

        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts)

        if not full_text.strip():
            raise ValueError(
                "No readable text found in the PDF. "
                "It may be a scanned document or contain only images."
            )

        return full_text, num_pages

    except ValueError:
        # Re-raise our own ValueErrors
        raise
    except Exception as e:
        raise ValueError(f"Could not read the PDF file: {e}")


def clean_text(text: str) -> str:
    """Clean extracted PDF text.

    - Collapses multiple whitespace/newlines
    - Removes non-printable characters
    - Strips leading/trailing whitespace
    """
    # Remove non-printable characters (keep newlines and tabs)
    text = re.sub(r"[^\S \n\t]+", " ", text)
    # Collapse multiple newlines into two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces into one
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[str]:
    """Split text into overlapping chunks.

    Args:
        text: The full document text.
        chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if not text.strip():
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Try to break at a sentence boundary (period, newline)
        if end < text_length:
            # Look for the last sentence-ending punctuation in the chunk
            break_point = max(
                text.rfind(". ", start, end),
                text.rfind(".\n", start, end),
                text.rfind("\n\n", start, end),
            )
            if break_point > start:
                end = break_point + 1  # include the period

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward, keeping overlap
        start = end - overlap if end < text_length else text_length

    return chunks
