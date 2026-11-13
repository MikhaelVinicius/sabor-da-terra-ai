from sabor_rag.service import ask_rag


def consultar_base_documental(pergunta: str) -> dict:
    """
    Consulta a base documental da Cooperativa Sabor da Terra.

    Deve ser utilizada para perguntas relacionadas a:
    - certificações;
    - contratos;
    - fichas técnicas;
    - inspeções;
    - informações documentais dos produtores.

    Retorna a resposta fundamentada e as fontes utilizadas.
    """

    if not pergunta or not pergunta.strip():
        return {
            "resposta": "Pergunta inválida.",
            "fontes": [],
        }

    result = ask_rag(pergunta.strip())

    return {
        "resposta": result.answer,
        "fontes": [
            {
                "arquivo": citation.source_path,
                "documento": citation.document_id,
                "trecho": citation.chunk_id,
            }
            for citation in result.citations
        ],
    }