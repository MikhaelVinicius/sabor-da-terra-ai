import re

from sabor_rag.models import DocumentChunk, SourceDocument


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_paragraphs(text: str) -> list[str]:
    normalized = _normalize_text(text)

    return [
        paragraph.strip()
        for paragraph in normalized.split("\n\n")
        if paragraph.strip()
    ]


def chunk_document(
    document: SourceDocument,
    max_chars: int = 1200,
    overlap_chars: int = 200,
) -> list[DocumentChunk]:
    paragraphs = _split_paragraphs(document.text)

    chunks_text: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = (
            f"{current}\n\n{paragraph}".strip()
            if current
            else paragraph
        )

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks_text.append(current)

        overlap = (
            current[-overlap_chars:]
            if current and overlap_chars > 0
            else ""
        )

        current = (
            f"{overlap}\n\n{paragraph}".strip()
            if overlap
            else paragraph
        )

        while len(current) > max_chars:
            chunks_text.append(current[:max_chars])

            start = max_chars - overlap_chars

            if start <= 0:
                start = max_chars

            current = current[start:]

    if current:
        chunks_text.append(current)

    chunks = []

    for index, text in enumerate(chunks_text):
        chunk_id = f"{document.document_id}::chunk-{index:04d}"

        metadata = {
            **document.metadata,
            "chunk_index": index,
        }

        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                text=text,
                source_path=document.source_path,
                category=document.category,
                metadata=metadata,
            )
        )

    return chunks


def chunk_documents(
    documents: list[SourceDocument],
    max_chars: int = 1200,
    overlap_chars: int = 200,
) -> list[DocumentChunk]:
    chunks = []

    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                max_chars=max_chars,
                overlap_chars=overlap_chars,
            )
        )

    return chunks