import chromadb

from sabor_rag.config import settings


def get_client() -> chromadb.PersistentClient:
    settings.db_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return chromadb.PersistentClient(
        path=str(settings.db_path)
    )


def get_collection():
    client = get_client()

    return client.get_or_create_collection(
        name=settings.collection_name,
        metadata={
            "hnsw:space": "cosine",
        },
    )


def reset_collection():
    client = get_client()

    try:
        client.delete_collection(
            name=settings.collection_name
        )
    except Exception:
        pass

    return client.get_or_create_collection(
        name=settings.collection_name,
        metadata={
            "hnsw:space": "cosine",
        },
    )