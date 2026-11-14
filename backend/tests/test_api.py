import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Multi-Document" in data["project_name"]

def test_kb_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_indexed" in data
    assert "total_chunks" in data
    assert "domain_title" in data

def test_query_validation():
    # Empty question
    response = client.post("/api/query", json={"question": "   "})
    assert response.status_code == 422 or response.status_code == 400

def test_valid_query_execution():
    response = client.post("/api/query", json={"question": "What is Retrieval Augmented Generation?", "top_k": 2})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "is_grounded" in data
    assert isinstance(data["is_grounded"], bool)

def test_multi_doc_analysis_execution():
    response = client.post("/api/analyze", json={"question": "Compare RAG architecture and chunking parameters across documents.", "top_k": 4})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "documents_considered" in data
    assert isinstance(data["documents_considered"], list)

def test_document_endpoint_valid_pdf():
    response = client.get("/api/documents/AI_RAG_Architecture_Paper.pdf")
    assert response.status_code == 200
    assert "application/pdf" in response.headers.get("content-type", "")
    assert "inline" in response.headers.get("content-disposition", "")
    assert len(response.content) > 500


def test_document_endpoint_serves_dataset_source_path(tmp_path, monkeypatch):
    from app.api import routes

    subject_root = tmp_path / "subject_materials"
    source_path = subject_root / "04_programming_and_data_structures" / "Example.pdf"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"%PDF-1.4 test fixture")
    monkeypatch.setattr(routes.settings, "SUBJECT_MATERIALS_DIR", subject_root)

    response = client.get(
        "/api/documents/Example.pdf",
        params={"source_path": str(source_path.resolve())},
    )

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 test fixture"


def test_document_endpoint_rejects_source_path_outside_allowed_roots(
    tmp_path, monkeypatch
):
    from app.api import routes

    subject_root = tmp_path / "subject_materials"
    subject_root.mkdir()
    outside_path = tmp_path / "Example.pdf"
    outside_path.write_bytes(b"%PDF-1.4 outside")
    monkeypatch.setattr(routes.settings, "SUBJECT_MATERIALS_DIR", subject_root)

    response = client.get(
        "/api/documents/Example.pdf",
        params={"source_path": str(outside_path.resolve())},
    )

    assert response.status_code == 400


def test_document_endpoint_not_found():
    response = client.get("/api/documents/non_existent_document_12345.pdf")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_document_endpoint_path_traversal():
    response = client.get("/api/documents/..%2Fmain.py")
    assert response.status_code == 400
    assert "traversal" in response.json()["detail"].lower()

def test_document_endpoint_non_pdf():
    response = client.get("/api/documents/chroma.sqlite3")
    assert response.status_code == 400
    assert "only pdf" in response.json()["detail"].lower()


def test_document_library_lists_real_index_state_without_paths(
    tmp_path, monkeypatch
):
    from app.api import routes
    from app.document_processing import library
    from app.document_processing.base import ExtractedDocument, ProcessedPage

    subject_root = tmp_path / "subject_materials"
    source_path = subject_root / "05_algorithms" / "Greedy_Algorithms.pdf"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"%PDF-1.4 fixture")
    monkeypatch.setattr(routes.settings, "DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr(routes.settings, "SUBJECT_MATERIALS_DIR", subject_root)
    monkeypatch.setattr(library, "_scan_signature", lambda: ("test-fixture",))
    monkeypatch.setattr(
        library,
        "_extract_repository",
        lambda signature: (
            ExtractedDocument(
                document_id="source-doc-id",
                document_name=source_path.name,
                source_path=str(source_path.resolve()),
                total_pages=5,
                pages=[
                    ProcessedPage(
                        page_number=1,
                        text="Greedy algorithms include the activity selection problem.",
                        metadata={"subject": "05_algorithms"},
                    )
                ],
                is_valid=True,
            ),
        ),
    )

    class FakeLibraryPipeline:
        def get_status(self):
            return {"total_chunks": 4}

        class vector_store:
            @staticmethod
            def get_document_records():
                return [
                    {
                        "source_path": str(source_path.resolve()),
                        "document_name": source_path.name,
                        "subject": "05_algorithms",
                        "page_count": 4,
                        "chunk_count": 4,
                    }
                ]

    monkeypatch.setattr(routes, "pipeline", FakeLibraryPipeline())
    response = client.get(
        "/api/library/documents",
        params={"search": "activity selection", "subject": "Algorithms"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] == 1
    assert data["indexed_documents"] == 1
    assert data["total_chunks"] == 4
    assert data["documents"][0]["indexed_status"] == "indexed"
    assert data["documents"][0]["page_count"] == 5
    assert data["documents"][0]["chunk_count"] == 4
    assert data["documents"][0]["subject"] == "Algorithms"
    assert "source_path" not in data["documents"][0]


def test_document_library_pdf_endpoint_uses_opaque_id_and_supports_download(
    tmp_path, monkeypatch
):
    from app.api import routes
    from app.document_processing.library import public_document_id

    subject_root = tmp_path / "subject_materials"
    source_path = subject_root / "04_programming" / "Original.pdf"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"%PDF-1.4 source bytes")
    monkeypatch.setattr(routes.settings, "DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr(routes.settings, "SUBJECT_MATERIALS_DIR", subject_root)
    document_id = public_document_id(str(source_path.resolve()))

    response = client.get(
        f"/api/library/documents/{document_id}/pdf?download=true"
    )

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 source bytes"
    assert response.headers["content-disposition"].startswith("attachment;")
    assert str(source_path) not in response.headers["content-disposition"]


def test_document_library_pdf_endpoint_rejects_non_opaque_ids():
    response = client.get("/api/library/documents/../../secret/pdf")
    assert response.status_code == 404
