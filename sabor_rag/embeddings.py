import os

from google import genai
from google.genai import types

from sabor_rag.config import settings


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada no ambiente."
        )

    return genai.Client(api_key=api_key)


def embed_document(text: str) -> list[float]:
    client = _get_client()

    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "A API não retornou embedding para o documento."
        )

    return response.embeddings[0].values


def embed_query(text: str) -> list[float]:
    client = _get_client()

    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "A API não retornou embedding para a consulta."
        )

    return response.embeddings[0].values