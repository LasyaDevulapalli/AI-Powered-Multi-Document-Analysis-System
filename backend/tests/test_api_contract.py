from fastapi.testclient import TestClient

from app.api import routes
from app.main import app


class FakePipeline:
    def answer_question(self, question, top_k):
        return self._response(question)

    def analyze_multi_document(self, question, top_k):
        return self._response(question)

    @staticmethod
    def _response(question):
        return {
            "question": question,
            "answer": "Evidence-based result [Evidence.pdf, p. 1].",
            "sources": [
                {
                    "document_name": "Evidence.pdf",
                    "page_number": 1,
                    "chunk_id": "chunk-1",
                    "relevance_score": 0.9,
                    "snippet": "Evidence passage.",
                    "source_path": "data/documents/Evidence.pdf",
                }
            ],
            "documents_considered": ["Evidence.pdf"],
            "retrieved_count": 1,
            "elapsed_time": 0.1,
            "is_grounded": True,
        }


def test_query_and_analysis_keep_existing_response_contract(monkeypatch):
    monkeypatch.setattr(routes, "pipeline", FakePipeline())
    client = TestClient(app)

    for endpoint in ("/api/query", "/api/analyze"):
        response = client.post(
            endpoint,
            json={"question": "Explain the concept", "top_k": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert set(
            (
                "question",
                "answer",
                "sources",
                "documents_considered",
                "retrieved_count",
                "elapsed_time",
                "is_grounded",
            )
        ).issubset(data)
        assert data["sources"][0]["source_path"] == "data/documents/Evidence.pdf"


def test_index_response_exposes_additive_corpus_summary_fields(monkeypatch):
    class FakeIndexPipeline:
        def index_documents(self, force_reindex=False):
            return {
                "status": "success",
                "message": "Indexed corpus.",
                "total_documents": 1,
                "valid_documents": 1,
                "failed_documents": 0,
                "total_chunks": 4,
                "elapsed_time": 0.1,
                "details": [],
                "pdfs_discovered": 1,
                "pdfs_extracted": 1,
                "pdfs_skipped": 0,
                "chunks_generated": 4,
                "chunks_indexed": 4,
                "subjects_represented": ["07_compiler_design"],
                "errors": 0,
            }

    monkeypatch.setattr(routes, "pipeline", FakeIndexPipeline())
    response = TestClient(app).post("/api/index", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["pdfs_discovered"] == 1
    assert data["chunks_indexed"] == 4
    assert data["subjects_represented"] == ["07_compiler_design"]
