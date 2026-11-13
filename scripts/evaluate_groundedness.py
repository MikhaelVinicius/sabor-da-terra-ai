import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from sabor_rag.service import ask_rag


GOLDEN_SET_PATH = Path(
    "data/golden_set/questions.json"
)


def load_golden_set() -> list[dict]:
    with GOLDEN_SET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main():
    golden_set = load_golden_set()

    total = len(golden_set)
    executed = 0
    infrastructure_failures = 0
    correct_source_count = 0

    print("=" * 60)
    print("AVALIAÇÃO DE GROUNDEDNESS")
    print("=" * 60)

    for item in golden_set:
        print()
        print("-" * 60)
        print(item["id"])
        print("-" * 60)
        print(
            f'Pergunta: {item["question"]}'
        )

        try:
            result = ask_rag(
                item["question"]
            )

        except Exception as exc:
            infrastructure_failures += 1

            print()
            print("ERRO DE EXECUÇÃO:")
            print(
                f"{type(exc).__name__}: {exc}"
            )
            print(
                "Este caso não foi avaliado por "
                "falha durante a execução."
            )

            continue

        executed += 1

        print()
        print("Resposta:")
        print(result.answer)

        print()
        print("Fontes utilizadas:")

        cited_sources = [
            citation.source_path
            for citation in result.citations
        ]

        if not cited_sources:
            print("Nenhuma fonte citada.")
        else:
            for source in cited_sources:
                print(f"- {source}")

        expected_source = item["expected_source"]

        source_correct = (
            expected_source in cited_sources
        )

        if source_correct:
            correct_source_count += 1
            print()
            print("Fonte esperada citada: SIM")
        else:
            print()
            print("Fonte esperada citada: NÃO")

    print()
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)

    print(
        f"Casos totais: {total}"
    )

    print(
        f"Casos executados: {executed}"
    )

    print(
        "Falhas de infraestrutura: "
        f"{infrastructure_failures}"
    )

    if executed > 0:
        citation_accuracy = (
            correct_source_count / executed
        )

        print(
            "Fonte esperada citada: "
            f"{correct_source_count}/{executed}"
        )

        print(
            "Taxa de citação correta: "
            f"{citation_accuracy:.2%}"
        )
    else:
        print(
            "Taxa de citação correta: "
            "não calculável"
        )


if __name__ == "__main__":
    main()