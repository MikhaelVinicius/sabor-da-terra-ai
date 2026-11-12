from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceDocument:
    document_id: str
    text: str
    source_path: str
    category: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    source_path: str
    category: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalHit:
    chunk: DocumentChunk
    score: float


@dataclass
class Citation:
    source_path: str
    document_id: str
    chunk_id: str
    excerpt: str


@dataclass
class RAGAnswer:
    answer: str
    citations: list[Citation]
    retrieval_hits: list[RetrievalHit] = field(default_factory=list)