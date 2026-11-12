import os
import time
from google.genai import errors, types
from google import genai
from google.genai import errors

from sabor_rag.config import settings


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada no ambiente."
        )

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=30000,
        ),
    )

def generate_answer(
    prompt: str,
    max_retries: int = 3,
) -> str:
    client = _get_client()

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=settings.generation_model,
                contents=prompt,
            )

            if not response.text:
                raise RuntimeError(
                    "O Gemini não retornou uma resposta."
                )

            return response.text.strip()

        except errors.ServerError as exc:
            if exc.code not in {503, 504}:
                raise

            if attempt == max_retries:
                raise RuntimeError(
                    "Gemini temporariamente indisponível "
                    "após múltiplas tentativas."
                ) from exc

            wait_seconds = 2 ** attempt

            print(
                f"Gemini indisponível (503). "
                f"Nova tentativa em {wait_seconds}s..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        "Não foi possível gerar a resposta."
    )