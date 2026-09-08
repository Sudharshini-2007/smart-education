"""
services/ai_service.py - LLM interface using Ollama.

Provides a modular AI service that communicates with Ollama's REST API
for both chat completions and text embeddings. Designed to be swappable
with other LLM providers in the future.
"""

import os
import json
import requests
from typing import List, Optional

from dotenv import load_dotenv

# Load .env if it exists (safe to call even if the file is missing)
load_dotenv()

# ---------------------------------------------------------------------------
def _get_config(key: str, default: str) -> str:
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


OLLAMA_BASE_URL = _get_config("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = _get_config("OLLAMA_MODEL", "mistral")
OLLAMA_EMBED_MODEL = _get_config("OLLAMA_EMBED_MODEL", "nomic-embed-text")


class AIService:
    """Wrapper around the Ollama REST API for chat and embeddings."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        chat_model: str = OLLAMA_MODEL,
        embed_model: str = OLLAMA_EMBED_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model

    # ----- Health check -----

    def check_available(self) -> bool:
        """Return True if the Ollama server is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    # ----- Chat -----

    def chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Send a chat completion request to Ollama.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}.
            system_prompt: Optional system-level instruction.

        Returns:
            The assistant's reply as a string.

        Raises:
            ConnectionError: If Ollama is unreachable.
            RuntimeError: If the API returns an error.
        """
        # Prepend system message if provided
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.chat_model,
            "messages": full_messages,
            "stream": False,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
            )
        except requests.ConnectionError:
            raise ConnectionError(
                "Cannot connect to Ollama. "
                "Please make sure Ollama is running (ollama serve)."
            )
        except requests.Timeout:
            raise RuntimeError(
                "Ollama took too long to respond. Please try again."
            )

        if resp.status_code != 200:
            raise RuntimeError(
                f"Ollama returned status {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        return data.get("message", {}).get("content", "").strip()

    # ----- Embeddings -----

    def get_embedding(self, text: str) -> List[float]:
        """Get the embedding vector for a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of floats (the embedding vector).
        """
        payload = {
            "model": self.embed_model,
            "input": text,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/embed",
                json=payload,
                timeout=60,
            )
        except requests.ConnectionError:
            raise ConnectionError(
                "Cannot connect to Ollama for embeddings. "
                "Please make sure Ollama is running."
            )

        if resp.status_code != 200:
            raise RuntimeError(
                f"Ollama embeddings error (status {resp.status_code}): "
                f"{resp.text}"
            )

        data = resp.json()
        # Ollama /api/embed returns {"embeddings": [[...]]}
        embeddings = data.get("embeddings", [])
        if embeddings:
            return embeddings[0]
        raise RuntimeError("Ollama returned empty embeddings.")

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts.

        Sends each text individually to avoid payload-size issues.

        Args:
            texts: List of text strings.

        Returns:
            A list of embedding vectors (one per text).
        """
        results = []
        for text in texts:
            results.append(self.get_embedding(text))
        return results
