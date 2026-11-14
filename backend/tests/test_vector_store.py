import pytest
from app.document_processing.base import DocumentChunk
from app.rag.vector_store import VectorStoreManager

def test_vector_store_add_and_query(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "VECTOR_STORE_DIR", tmp_path)
    store = VectorStoreManager(collection_name="test_temp_collection")

    chunk1 = DocumentChunk(
        chunk_id="chk_1",
        document_id="doc_1",
        document_name="RAG_Paper.pdf",
        page_number=1,
        content="Retrieval Augmented Generation combines vector search with language generation.",
        source_path="/data/RAG_Paper.pdf",
        metadata={"document_name": "RAG_Paper.pdf", "page_number": 1, "chunk_id": "chk_1"}
    )
    
    # Dummy embedding vector of dimension 4
    dummy_embedding = [0.1, 0.2, 0.3, 0.4]
    
    added = store.add_chunks([chunk1], [dummy_embedding])
    assert added == 1

    status = store.get_status()
    assert status["is_indexed"] is True
    assert status["total_chunks"] == 1
    assert "RAG_Paper.pdf" in status["document_names"]

    # Query with similar dummy vector
    results = store.query(query_embedding=[0.1, 0.2, 0.3, 0.4], top_k=1)
    assert len(results) == 1
    assert results[0]["document_name"] == "RAG_Paper.pdf"
    assert results[0]["chunk_id"] == "chk_1"
    assert results[0]["source_path"] == "/data/RAG_Paper.pdf"
