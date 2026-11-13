from sabor_rag.chunking import chunk_document, chunk_documents
from sabor_rag.loader import load_documents


def test_chunking_generates_chunks():
    documents = load_documents()

    chunks = chunk_documents(documents)

    assert len(chunks) > 0


def test_chunk_has_required_fields():
    documents = load_documents()

    chunks = chunk_documents(documents)

    chunk = chunks[0]

    assert chunk.chunk_id
    assert chunk.document_id
    assert chunk.text
    assert chunk.source_path
    assert chunk.category


def test_chunk_ids_are_unique():
    documents = load_documents()

    chunks = chunk_documents(documents)

    chunk_ids = [
        chunk.chunk_id
        for chunk in chunks
    ]

    assert len(chunk_ids) == len(set(chunk_ids))


def test_josefa_generates_chunks():
    documents = load_documents()

    josefa = next(
        document
        for document in documents
        if document.metadata.get("producer_id") == "P008"
    )

    chunks = chunk_document(josefa)

    assert len(chunks) > 0

    assert all(
        chunk.document_id == josefa.document_id
        for chunk in chunks
    )


def test_josefa_critical_information_is_preserved():
    documents = load_documents()

    josefa = next(
        document
        for document in documents
        if document.metadata.get("producer_id") == "P008"
    )

    chunks = chunk_document(josefa)

    combined_text = "\n".join(
        chunk.text
        for chunk in chunks
    )

    assert "30/09/2026" in combined_text
    assert "VENCIDA" in combined_text.upper()
    assert "renovação" in combined_text.lower()


def test_sensitive_data_remains_redacted_after_chunking():
    documents = load_documents()

    josefa = next(
        document
        for document in documents
        if document.metadata.get("producer_id") == "P008"
    )

    chunks = chunk_document(josefa)

    combined_text = "\n".join(
        chunk.text
        for chunk in chunks
    )

    assert "[CPF_REDACTED]" in combined_text