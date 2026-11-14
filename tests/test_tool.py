from unittest.mock import patch

from sabor_rag.models import (
    Citation,
    RAGAnswer,
)
from sabor_rag.tool import consultar_base_documental


def test_consultar_base_documental_returns_expected_structure():
    fake_answer = RAGAnswer(
        answer=(
            "A certificação de Josefa está vencida "
            "e encontra-se em processo de renovação."
        ),
        citations=[
            Citation(
                source_path=(
                    "certificacoes/"
                    "cert_organica_josefa_souza_P008.txt"
                ),
                document_id=(
                    "certificacoes/"
                    "cert_organica_josefa_souza_P008"
                ),
                chunk_id=(
                    "certificacoes/"
                    "cert_organica_josefa_souza_P008"
                    "::chunk-0000"
                ),
                excerpt=(
                    "Certificação vencida em "
                    "30/09/2026."
                ),
            )
        ],
    )

    with patch(
        "sabor_rag.tool.ask_rag",
        return_value=fake_answer,
    ):
        result = consultar_base_documental(
            "Qual é a situação da certificação "
            "de Josefa?"
        )

    assert "resposta" in result
    assert "fontes" in result

    assert result["resposta"] == fake_answer.answer

    assert len(result["fontes"]) == 1

    assert result["fontes"][0]["arquivo"] == (
        "certificacoes/"
        "cert_organica_josefa_souza_P008.txt"
    )

    assert result["fontes"][0]["documento"] == (
        "certificacoes/"
        "cert_organica_josefa_souza_P008"
    )

    assert result["fontes"][0]["trecho"] == (
        "certificacoes/"
        "cert_organica_josefa_souza_P008"
        "::chunk-0000"
    )


def test_consultar_base_documental_rejects_empty_question():
    result = consultar_base_documental("   ")

    assert result == {
        "resposta": "Pergunta inválida.",
        "fontes": [],
    }