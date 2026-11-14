import re

from sabor_rag.generator import generate_answer
from sabor_rag.models import Citation, RAGAnswer
from sabor_rag.prompting import build_prompt
from sabor_rag.retriever import retrieve

def _extract_source_numbers(
    answer_text: str,
) -> set[int]:
    source_numbers = set()

    citation_groups = re.findall(
        r"\[([^\]]*FONTE[^\]]*)\]",
        answer_text,
        flags=re.IGNORECASE,
    )

    for group in citation_groups:
        numbers = re.findall(
            r"FONTE\s*(\d+)",
            group,
            flags=re.IGNORECASE,
        )

        source_numbers.update(
            int(number)
            for number in numbers
        )

    return source_numbers


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

    source_numbers = _extract_source_numbers(
    answer_text
)

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