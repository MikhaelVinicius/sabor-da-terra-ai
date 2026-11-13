import re

from sabor_rag.generator import generate_answer
from sabor_rag.models import Citation, RAGAnswer
from sabor_rag.prompting import build_prompt
from sabor_rag.retriever import retrieve


def ask_rag(question: str) -> RAGAnswer:
    hits = retrieve(question)

    if not hits:
        return RAGAnswer(
            answer="Informação não encontrada na base documental.",
            citations=[],
            retrieval_hits=[],
        )

    prompt = build_prompt(
        question=question,
        hits=hits,
    )

    answer_text = generate_answer(prompt)

    if answer_text.strip().lower().startswith(
        "informação não encontrada na base documental"
    ):
        return RAGAnswer(
            answer=answer_text,
            citations=[],
            retrieval_hits=hits,
        )

    source_numbers = {
        int(number)
        for number in re.findall(
            r"\[FONTE\s*(\d+)\]",
            answer_text,
            flags=re.IGNORECASE,
        )
    }

    citations = []
    seen_sources = set()

    for source_number in sorted(source_numbers):
        index = source_number - 1

        if index < 0 or index >= len(hits):
            continue

        hit = hits[index]

        if hit.chunk.source_path in seen_sources:
            continue

        seen_sources.add(hit.chunk.source_path)

        citations.append(
            Citation(
                source_path=hit.chunk.source_path,
                document_id=hit.chunk.document_id,
                chunk_id=hit.chunk.chunk_id,
                excerpt=hit.chunk.text[:300],
            )
        )

    return RAGAnswer(
        answer=answer_text,
        citations=citations,
        retrieval_hits=hits,
    )