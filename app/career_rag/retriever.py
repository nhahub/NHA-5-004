"""Query-time retrieval ONLY: embed the question, fetch top-k chunks. No generation here."""
from app.career_rag.embedder import embed_text
from app.career_rag.vector_store import query
from app.career_rag.ingestion import COLLECTION_NAME


def retrieve_relevant_chunks(question: str, top_k: int = 5) -> list[str]:
    query_embedding = embed_text([question])[0]
    result = query(COLLECTION_NAME, query_embedding, top_k)
    return result["documents"][0] if result["documents"] else []


def retrieve_resources(topic: str, top_k: int = 3) -> list[dict]:
    """Suggested-resources lookup for a topic: real chunks + their source URL, for
    optional display alongside an interview-prep plan day. Returns [] if nothing
    has been ingested yet — callers should treat that as 'no suggestions', not an error."""
    query_embedding = embed_text([topic])[0]
    result = query(COLLECTION_NAME, query_embedding, top_k)
    if not result["documents"] or not result["documents"][0]:
        return []
    chunks = result["documents"][0]
    metadatas = result["metadatas"][0]
    return [{"excerpt": chunk, "source_url": meta.get("source_url")} for chunk, meta in zip(chunks, metadatas)]
