import pytest
from app.document_processing.base import ExtractedDocument, ProcessedPage
from app.rag.chunker import TextChunker

def test_text_chunker_basic():
    doc = ExtractedDocument(
        document_id="test_doc_1",
        document_name="Sample_Academic_Paper.pdf",
        source_path="/data/documents/Sample_Academic_Paper.pdf",
        total_pages=1,
        pages=[
            ProcessedPage(
                page_number=1,
                text="Retrieval Augmented Generation enhances LLMs by retrieving relevant domain document chunks. " * 10
            )
        ]
    )

    chunker = TextChunker(chunk_size=200, chunk_overlap=30)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.document_name == "Sample_Academic_Paper.pdf"
        assert chunk.page_number == 1
        assert chunk.document_id == "test_doc_1"
        assert chunk.chunk_id.startswith("test_doc_1_p1_c")
        assert len(chunk.content) <= 200 + 50
