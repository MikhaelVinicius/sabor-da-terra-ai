from sabor_rag.config import settings
from sabor_rag.embeddings import embed_query
from sabor_rag.models import DocumentChunk, RetrievalHit
from sabor_rag.vector_store import get_collection


def retrieve(
    query: str,
    top_k: int | None = None,
) -> list[RetrievalHit]:
    collection = get_collection()

    query_embedding = embed_query(query)

    limit = top_k or settings.top_k

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    hits = []

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for chunk_id, text, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
    ):
        score = 1.0 - float(distance)

        if score < settings.min_score:
            continue

        chunk = DocumentChunk(
            chunk_id=chunk_id,
            document_id=metadata["document_id"],
            text=text,
            source_path=metadata["source_path"],
            category=metadata["category"],
            metadata=dict(metadata),
        )

        hits.append(
            RetrievalHit(
                chunk=chunk,
                score=score,
            )
        )

    return hits