"""ChromaDB helpers shared by all Altair8 agents."""
import os
import chromadb


def get_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(
        host=os.environ.get("CHROMA_HOST", "chromadb"),
        port=int(os.environ.get("CHROMA_PORT", "8000")),
    )


def get_collection(name: str):
    client = get_client()
    return client.get_or_create_collection(name=name)


def remember(collection_name: str, doc_id: str, text: str, metadata: dict | None = None) -> None:
    collection = get_collection(collection_name)
    collection.upsert(ids=[doc_id], documents=[text], metadatas=[metadata or {}])


def recall(collection_name: str, query: str, n_results: int = 5):
    collection = get_collection(collection_name)
    return collection.query(query_texts=[query], n_results=n_results)
