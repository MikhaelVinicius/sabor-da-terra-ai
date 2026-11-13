from sabor_rag.loader import load_documents


def test_loads_all_documents():
    documents = load_documents()

    assert len(documents) == 20


def test_document_categories():
    documents = load_documents()

    categories = {
        document.category
        for document in documents
    }

    assert "certificacoes" in categories
    assert "contratos" in categories
    assert "fichas_tecnicas" in categories


def test_josefa_document_is_loaded():
    documents = load_documents()

    josefa = next(
        document
        for document in documents
        if document.metadata.get("producer_id") == "P008"
    )

    assert (
        josefa.source_path
        == "certificacoes/cert_organica_josefa_souza_P008.txt"
    )

    assert "Josefa Alves de Souza" in josefa.text


def test_sensitive_cpf_is_redacted():
    documents = load_documents()

    josefa = next(
        document
        for document in documents
        if document.metadata.get("producer_id") == "P008"
    )

    assert "[CPF_REDACTED]" in josefa.text


def test_josefa_expiration_date_is_preserved():
    documents = load_documents()

    josefa = next(
        document
        for document in documents
        if document.metadata.get("producer_id") == "P008"
    )

    assert "30/09/2026" in josefa.text