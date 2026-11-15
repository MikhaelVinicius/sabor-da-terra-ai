"""Cliente Gemini usado pelo orquestrador."""
from __future__ import annotations

from functools import lru_cache

from google import genai

from core import config


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    if config.GEMINI_API_KEY:
        return genai.Client(api_key=config.GEMINI_API_KEY)
    if config.GCP_PROJECT:
        return genai.Client(vertexai=True, project=config.GCP_PROJECT, location=config.GCP_LOCATION)
    raise RuntimeError("Defina GEMINI_API_KEY (ou GOOGLE_CLOUD_PROJECT para Vertex AI). Veja .env.example.")


def backend_descricao() -> str:
    if config.GEMINI_API_KEY:
        return f"Gemini API · {config.GEMINI_MODEL}"
    return f"Vertex AI ({config.GCP_PROJECT}) · {config.GEMINI_MODEL}"
