from sabor_rag.models import DocumentChunk, RetrievalHit
from sabor_rag.prompting import build_context, build_prompt
from sabor_rag.service import _extract_source_numbers

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

def test_source_reference_regex_accepts_optional_spaces():
    import re

    examples = [
        "[FONTE 1]",
        "[FONTE1]",
        "[FONTE   1]",
    ]

    for example in examples:
        matches = re.findall(
            r"\[FONTE\s*(\d+)\]",
            example,
            flags=re.IGNORECASE,
        )

        assert matches == ["1"]

def test_extract_source_numbers_accepts_multiple_formats():
    cases = {
        "[FONTE 1]": {1},
        "[FONTE1]": {1},
        "[FONTE   1]": {1},
        "[FONTE 1, FONTE 2]": {1, 2},
        "[FONTE 2, FONTE 3, FONTE 5]": {2, 3, 5},
        "Resposta baseada em [FONTE 1] e [FONTE 4]": {1, 4},
    }

    for text, expected in cases.items():
        assert _extract_source_numbers(text) == expected


from scripts.evaluate_groundedness import evaluate_expected_terms


def test_evaluate_expected_terms():
    answer = (
        "A certificação está expirada desde 30/09/2026 "
        "e encontra-se em processo de renovação. "
        "Os produtos não podem ser comercializados como orgânicos."
    )

    expected_terms = [
        ["vencida", "expirada"],
        ["30/09/2026"],
        ["renovação"],
        ["não podem ser comercializados como orgânicos"],
    ]

    matched, total = evaluate_expected_terms(
        answer,
        expected_terms,
    )

    assert matched == 4
    assert total == 4