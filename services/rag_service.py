"""
services/rag_service.py - Retrieval-Augmented Generation service.

Manages the FAISS vector index for uploaded study material:
- Build an index from text chunks + embeddings
- Search for the most relevant chunks given a query
- Generate suggested questions from the material
"""

import re
from typing import List, Optional

import numpy as np

from services.prompt_templates import get_template, SYSTEM_RAG


class RAGService:
    """In-memory RAG index backed by FAISS."""

    def __init__(self):
        self.index = None          # FAISS index
        self.chunks: List[str] = []  # The text chunks (aligned with index rows)
        self.dimension: int = 0     # Embedding dimension

    @property
    def is_ready(self) -> bool:
        """True if an index has been built and is searchable."""
        return self.index is not None and len(self.chunks) > 0

    # -----------------------------------------------------------------
    # Index building
    # -----------------------------------------------------------------

    def build_index(self, chunks: List[str], ai_service) -> None:
        """Embed all chunks and build a FAISS index.

        Args:
            chunks: List of text chunks from the PDF.
            ai_service: An AIService instance (used for embeddings).
        """
        try:
            import faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu is not installed. Run: pip install faiss-cpu"
            )

        if not chunks:
            raise ValueError("No text chunks to index.")

        # Get embeddings for every chunk
        embeddings = ai_service.get_embeddings_batch(chunks)

        # Convert to numpy array
        matrix = np.array(embeddings, dtype="float32")
        self.dimension = matrix.shape[1]

        # Build a flat L2 index (exact search — fast enough for document-level)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(matrix)
        self.chunks = list(chunks)

    # -----------------------------------------------------------------
    # Search
    # -----------------------------------------------------------------

    def search(
        self,
        query: str,
        ai_service,
        top_k: int = 3,
    ) -> List[str]:
        """Retrieve the most relevant chunks for a query.

        Args:
            query: The student's question.
            ai_service: An AIService instance (used for query embedding).
            top_k: Number of chunks to return.

        Returns:
            A list of the most relevant text chunks.
        """
        if not self.is_ready:
            return []

        query_vec = np.array(
            [ai_service.get_embedding(query)], dtype="float32"
        )
        distances, indices = self.index.search(query_vec, min(top_k, len(self.chunks)))

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results

    # -----------------------------------------------------------------
    # Suggested questions
    # -----------------------------------------------------------------

    def generate_suggested_questions(
        self,
        ai_service,
        max_context_chunks: int = 6,
    ) -> List[str]:
        """Use the LLM to generate suggested questions from the material.

        Args:
            ai_service: An AIService instance.
            max_context_chunks: How many chunks to include as context.

        Returns:
            A list of 5 suggested question strings.
        """
        if not self.chunks:
            return []

        # Use a sample of chunks spread across the document
        step = max(1, len(self.chunks) // max_context_chunks)
        sample = self.chunks[::step][:max_context_chunks]
        context = "\n\n---\n\n".join(sample)

        template = get_template("suggested_questions")
        prompt = template.format(context=context)

        try:
            response = ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a helpful study assistant. Generate exactly 5 questions.",
            )

            # Parse numbered lines from the response
            questions = []
            for line in response.strip().split("\n"):
                line = line.strip()
                # Match lines starting with a number + period/parenthesis
                cleaned = re.sub(r"^\d+[\.\)\-]\s*", "", line)
                if cleaned and len(cleaned) > 5:
                    questions.append(cleaned)

            return questions[:5] if questions else []

        except Exception:
            return []

    # -----------------------------------------------------------------
    # RAG-powered answer
    # -----------------------------------------------------------------

    def answer_question(
        self,
        question: str,
        ai_service,
        template_name: str = "rag_answer",
        chat_history: Optional[List[dict]] = None,
        extra_vars: Optional[dict] = None,
    ) -> str:
        """Retrieve context and generate an answer using the LLM.

        Args:
            question: The student's question.
            ai_service: An AIService instance.
            template_name: Which prompt template to use.
            chat_history: Previous messages for conversation continuity.
            extra_vars: Additional variables to inject into the template
                        (e.g. student_answer for evaluate_answer template).

        Returns:
            The AI-generated answer string.
        """
        # Retrieve relevant context
        context_chunks = self.search(question, ai_service, top_k=3)
        context = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant context found in the uploaded material."

        # Build the prompt from the template
        template = get_template(template_name)
        format_vars = {"context": context, "question": question}
        if extra_vars:
            format_vars.update(extra_vars)
        prompt = template.format(**format_vars)

        # Build message list (include history for follow-up context)
        messages = []
        if chat_history:
            # Include recent history for conversational context
            messages.extend(chat_history[-6:])  # Keep last 3 exchanges
        messages.append({"role": "user", "content": prompt})

        return ai_service.chat(messages=messages, system_prompt=SYSTEM_RAG)
