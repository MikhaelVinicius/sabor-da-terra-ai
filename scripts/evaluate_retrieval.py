import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from sabor_rag.retriever import retrieve


GOLDEN_SET_PATH = Path(
    "data/golden_set/questions.json"
)


def load_golden_set() -> list[dict]:
    with GOLDEN_SET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def evaluate_question(
    item: dict,
) -> dict:
    hits = retrieve(
        item["question"],
        top_k=5,
    )

    retrieved_sources = [
        hit.chunk.source_path
        for hit in hits
    ]

    expected_source = item["expected_source"]

    hit_at_1 = (
        expected_source in retrieved_sources[:1]
    )

    hit_at_3 = (
        expected_source in retrieved_sources[:3]
    )

    hit_at_5 = (
        expected_source in retrieved_sources[:5]
    )

    rank = None

    if expected_source in retrieved_sources:
        rank = (
            retrieved_sources.index(expected_source)
            + 1
        )

    return {
        "id": item["id"],
        "question": item["question"],
        "expected_source": expected_source,
        "retrieved_sources": retrieved_sources,
        "rank": rank,
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
    }


def main():
    golden_set = load_golden_set()

    results = [
        evaluate_question(item)
        for item in golden_set
    ]

    total = len(results)

    if total == 0:
        print("Golden Set vazio.")
        return

    hits_at_1 = sum(
        result["hit_at_1"]
        for result in results
    )

    hits_at_3 = sum(
        result["hit_at_3"]
        for result in results
    )

    hits_at_5 = sum(
        result["hit_at_5"]
        for result in results
    )

    print("=" * 60)
    print("AVALIAÇÃO DO RETRIEVAL")
    print("=" * 60)

    for result in results:
        status = (
            "OK"
            if result["hit_at_1"]
            else "ERRO"
        )

        print()
        print(
            f'{result["id"]} - {status}'
        )
        print(
            f'Pergunta: {result["question"]}'
        )
        print(
            f'Esperado: {result["expected_source"]}'
        )
        print(
            f'Rank: {result["rank"]}'
        )

    print()
    print("=" * 60)
    print("MÉTRICAS")
    print("=" * 60)

    print(
        f"Hit@1: {hits_at_1}/{total} "
        f"({hits_at_1 / total:.2%})"
    )

    print(
        f"Hit@3: {hits_at_3}/{total} "
        f"({hits_at_3 / total:.2%})"
    )

    print(
        f"Hit@5: {hits_at_5}/{total} "
        f"({hits_at_5 / total:.2%})"
    )


if __name__ == "__main__":
    main()