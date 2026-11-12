from sabor_rag.chunking import chunk_documents
from sabor_rag.embeddings import embed_document
from sabor_rag.loader import load_documents
from sabor_rag.vector_store import reset_collection


def build_index() -> int:
    documents = load_documents()
    chunks = chunk_documents(documents)

    collection = reset_collection()

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"Indexando {index}/{len(chunks)}: "
            f"{chunk.chunk_id}"
        )

        embedding = embed_document(chunk.text)

        metadata = {
            "document_id": chunk.document_id,
            "source_path": chunk.source_path,
            "category": chunk.category,
            "chunk_index": chunk.metadata.get(
                "chunk_index",
                index - 1,
            ),
        }

        producer_id = chunk.metadata.get("producer_id")

        if producer_id:
            metadata["producer_id"] = producer_id

        collection.add(
            ids=[chunk.chunk_id],
            embeddings=[embedding],
            documents=[chunk.text],
            metadatas=[metadata],
        )

    return collection.count()