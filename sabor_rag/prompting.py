from sabor_rag.models import RetrievalHit


def build_context(hits: list[RetrievalHit]) -> str:
    if not hits:
        return "Nenhum documento relevante foi encontrado."

    sections = []

    for index, hit in enumerate(hits, start=1):
        section = (
            f"[FONTE {index}]\n"
            f"Arquivo: {hit.chunk.source_path}\n"
            f"Documento: {hit.chunk.document_id}\n"
            f"Trecho: {hit.chunk.chunk_id}\n"
            f"Relevância: {hit.score:.4f}\n\n"
            f"{hit.chunk.text}"
        )

        sections.append(section)

    return "\n\n---\n\n".join(sections)


def build_prompt(
    question: str,
    hits: list[RetrievalHit],
) -> str:
    context = build_context(hits)

    return f"""
Você é o assistente documental da Cooperativa Sabor da Terra.

Sua função é responder perguntas exclusivamente com base na base documental fornecida.

REGRAS OBRIGATÓRIAS:

1. Utilize somente informações presentes nas fontes fornecidas abaixo.

2. Não invente, complete ou suponha informações que não estejam explicitamente presentes nas fontes.

3. Se as fontes não contiverem informação suficiente para responder, responda:
"Informação não encontrada na base documental."

4. Diferencie cuidadosamente os estados de documentos, certificações e contratos.

5. Não considere uma certificação válida apenas porque existe um documento de certificação.

6. Expressões como "vencida", "expirada", "em renovação", "renovação solicitada" ou equivalentes devem ser preservadas na interpretação.

7. Uma certificação em processo de renovação não deve ser apresentada como válida, a menos que uma fonte declare explicitamente sua validade atual.

8. Quando houver conflito entre fontes, informe que existe divergência documental e não escolha uma versão sem evidência.

9. Não exponha dados que estejam marcados como [CPF_REDACTED], [TELEFONE_REDACTED], [CONTA_REDACTED], [AGENCIA_REDACTED] ou [LINHA_PIX_REDACTED].

10. Responda de forma objetiva e em português brasileiro.

11. Ao fundamentar a resposta, indique as fontes utilizando os identificadores [FONTE 1], [FONTE 2] etc.

PERGUNTA:
{question}

FONTES DOCUMENTAIS:
{context}

RESPOSTA:
""".strip()