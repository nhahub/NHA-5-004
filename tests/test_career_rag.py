"""Unit tests for app/career_rag/: chunking logic in ingestion.py, retriever.py query shape (vector store mocked)."""
from app.career_rag.ingestion import _chunk_text
from app.career_rag import retriever


def test_chunk_text_shorter_than_chunk_size_returns_one_chunk():
    text = "short text"
    chunks = _chunk_text(text, chunk_size=800, overlap=100)
    assert chunks == [text]


def test_chunk_text_respects_overlap():
    text = "a" * 1000
    chunks = _chunk_text(text, chunk_size=800, overlap=100)
    assert len(chunks) == 2
    assert chunks[0] == text[0:800]
    assert chunks[1] == text[700:1000]


def test_chunk_text_covers_full_text_with_no_gaps():
    text = "0123456789" * 50  # 500 chars
    chunk_size, overlap = 120, 20
    chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    step = chunk_size - overlap
    for i, chunk in enumerate(chunks):
        start = i * step
        assert chunk == text[start:start + chunk_size]
    assert chunks[-1] != ""


def test_retrieve_relevant_chunks_returns_documents(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {"documents": [["chunk a", "chunk b"]]},
    )
    result = retriever.retrieve_relevant_chunks("what should I study?", top_k=2)
    assert result == ["chunk a", "chunk b"]


def test_retrieve_relevant_chunks_handles_empty_results(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {"documents": []},
    )
    result = retriever.retrieve_relevant_chunks("anything")
    assert result == []


def test_retrieve_resources_pairs_chunks_with_source_urls(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {
            "documents": [["chunk a", "chunk b"]],
            "metadatas": [[{"source_url": "https://a.example"}, {"source_url": "https://b.example"}]],
        },
    )
    result = retriever.retrieve_resources("system design")
    assert result == [
        {"excerpt": "chunk a", "source_url": "https://a.example"},
        {"excerpt": "chunk b", "source_url": "https://b.example"},
    ]


def test_retrieve_resources_handles_empty_results(monkeypatch):
    monkeypatch.setattr(retriever, "embed_text", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retriever, "query",
        lambda collection_name, query_embedding, top_k: {"documents": []},
    )
    result = retriever.retrieve_resources("anything")
    assert result == []
