from sabor_rag.models import DocumentChunk, RetrievalHit
from sabor_rag.prompting import build_context, build_prompt


def _create_test_hit() -> RetrievalHit:
    chunk = DocumentChunk(
        chunk_id="certificacoes/teste::chunk-0000",
        document_id="certificacoes/teste",
        text=(
            "Certificação vencida em 30/09/2026. "
            "Processo de renovação em andamento."
        ),
        source_path="certificacoes/teste.txt",
        category="certificacoes",
        metadata={
            "producer_id": "P008",
            "chunk_index": 0,
        },
    )

    return RetrievalHit(
        chunk=chunk,
        score=0.85,
    )


def test_context_contains_source_information():
    hit = _create_test_hit()

    context = build_context([hit])

    assert "[FONTE 1]" in context
    assert "certificacoes/teste.txt" in context
    assert "Certificação vencida" in context


def test_context_without_hits():
    context = build_context([])

    assert (
        context
        == "Nenhum documento relevante foi encontrado."
    )


def test_prompt_contains_question():
    hit = _create_test_hit()

    question = (
        "Qual é a situação da certificação?"
    )

    prompt = build_prompt(
        question=question,
        hits=[hit],
    )

    assert question in prompt


def test_prompt_contains_document_context():
    hit = _create_test_hit()

    prompt = build_prompt(
        question="Qual é a situação?",
        hits=[hit],
    )

    assert "Certificação vencida" in prompt
    assert "[FONTE 1]" in prompt


def test_prompt_requires_grounded_answer():
    hit = _create_test_hit()

    prompt = build_prompt(
        question="Qual é a situação?",
        hits=[hit],
    )

    assert (
        "Informação não encontrada na base documental."
        in prompt
    )


def test_prompt_does_not_treat_renewal_as_valid():
    hit = _create_test_hit()

    prompt = build_prompt(
        question="A certificação está válida?",
        hits=[hit],
    )

    assert (
        "em processo de renovação não deve ser "
        "apresentada como válida"
        in prompt
    )