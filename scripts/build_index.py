from sabor_rag.indexer import build_index


if __name__ == "__main__":
    total = build_index()

    print()
    print(f"Indexação concluída.")
    print(f"Total de chunks indexados: {total}")