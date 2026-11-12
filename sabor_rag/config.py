from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


@dataclass(frozen=True)
class RAGSettings:
    docs_dir: Path = Path(os.getenv("RAG_DOCS_DIR", "data/documents"))
    db_path: Path = Path(os.getenv("RAG_DB_PATH", "data/chroma"))
    collection_name: str = os.getenv("RAG_COLLECTION", "sabor_da_terra_docs")
    embedding_model: str = os.getenv(
        "RAG_EMBEDDING_MODEL",
        "gemini-embedding-001"
    )
    generation_model: str = os.getenv(
        "RAG_GENERATION_MODEL",
        "gemini-3.8-flash"
    )
    top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    min_score: float = float(os.getenv("RAG_MIN_SCORE", "0.30"))
    redact_sensitive: bool = _as_bool(
        os.getenv("RAG_REDACT_SENSITIVE"),
        True
    )


settings = RAGSettings()