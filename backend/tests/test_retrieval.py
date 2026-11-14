from app.document_processing.base import DocumentChunk
from app.rag.vector_store import VectorStoreManager


class FakeCollection:
    def __init__(self, rows):
        self.rows = rows

    def count(self):
        return len(self.rows)

    def query(self, **kwargs):
        return {
            "ids": [[row["id"] for row in self.rows]],
            "documents": [[row["content"] for row in self.rows]],
            "metadatas": [[row["metadata"] for row in self.rows]],
            "distances": [[row["distance"] for row in self.rows]],
        }


def _row(chunk_id, name, content, distance, page=1):
    return {
        "id": chunk_id,
        "content": content,
        "distance": distance,
        "metadata": {
            "document_name": name,
            "page_number": page,
            "chunk_id": chunk_id,
            "source_path": f"data/documents/{name}",
        },
    }


def _manager(rows):
    manager = object.__new__(VectorStoreManager)
    manager.collection = FakeCollection(rows)
    manager.collection_name = "in-memory-test"
    return manager


def test_bm25_favors_chunks_with_matching_query_terms():
    scores = VectorStoreManager._bm25_scores(
        {"dijkstra", "shortest", "path"},
        [
            "A general graph traversal overview.",
            "Dijkstra algorithm finds shortest paths in a weighted graph.",
        ],
    )

    assert scores[1] > scores[0]


def test_hybrid_query_fuses_ranks_and_preserves_source_metadata():
    store = _manager(
        [
            _row(
                "semantic-hit",
                "Graph_Notes.pdf",
                "A graph traversal overview and notes on search.",
                0.05,
                page=2,
            ),
            _row(
                "lexical-hit",
                "Shortest_Path.pdf",
                "Dijkstra algorithm finds the shortest path in a graph.",
                0.30,
                page=7,
            ),
            _row(
                "irrelevant",
                "Other.pdf",
                "Unrelated material.",
                1.10,
            ),
        ]
    )

    results = store.query(
        query_embedding=[0.0],
        question="Dijkstra algorithm shortest path",
        top_k=2,
    )

    assert {item["chunk_id"] for item in results} == {
        "semantic-hit",
        "lexical-hit",
    }
    lexical_hit = next(item for item in results if item["chunk_id"] == "lexical-hit")
    assert lexical_hit["semantic_rank"] == 2
    assert lexical_hit["lexical_rank"] == 1
    assert lexical_hit["document_name"] == "Shortest_Path.pdf"
    assert lexical_hit["page_number"] == 7
    assert lexical_hit["source_path"] == "data/documents/Shortest_Path.pdf"


def test_multi_document_query_prioritizes_distinct_relevant_documents():
    store = _manager(
        [
            _row(
                "doc-a-1",
                "Doc_A.pdf",
                "Dijkstra shortest path algorithm in graph traversal.",
                0.05,
                page=1,
            ),
            _row(
                "doc-a-2",
                "Doc_A.pdf",
                "Dijkstra algorithm and shortest path implementation.",
                0.20,
                page=2,
            ),
            _row(
                "doc-b-1",
                "Doc_B.pdf",
                "Dijkstra algorithm finds the shortest path.",
                0.40,
                page=4,
            ),
            _row(
                "noise",
                "Noise.pdf",
                "Unrelated material.",
                1.10,
            ),
        ]
    )

    results = store.query(
        query_embedding=[0.0],
        question="Dijkstra algorithm shortest path",
        top_k=2,
        diversify_documents=True,
    )

    assert len(results) == 2
    assert len({item["document_name"] for item in results}) == 2
    assert {item["document_name"] for item in results} == {
        "Doc_A.pdf",
        "Doc_B.pdf",
    }


def test_query_tokens_retain_numeric_and_algorithmic_identifiers():
    tokens = VectorStoreManager._tokens("Evaluate O(n log n) for 3.14 inputs")

    assert {"n", "o", "3.14"}.issubset(tokens)


def test_add_chunks_skips_existing_records_without_replacing_them():
    class ExistingCollection:
        def __init__(self):
            self.rows = {"existing-chunk": "original document body"}
            self.add_calls = []

        def get(self, ids, include):
            return {"ids": [chunk_id for chunk_id in ids if chunk_id in self.rows]}

        def add(self, **kwargs):
            self.add_calls.append(kwargs)
            for chunk_id, body in zip(kwargs["ids"], kwargs["documents"]):
                self.rows[chunk_id] = body

    store = object.__new__(VectorStoreManager)
    store.collection_name = "in-memory-test"
    store.collection = ExistingCollection()
    existing_chunk = DocumentChunk(
        chunk_id="existing-chunk",
        document_id="doc",
        document_name="Evidence.pdf",
        page_number=1,
        content="new document body",
        source_path="data/documents/Evidence.pdf",
        metadata={"document_name": "Evidence.pdf"},
    )
    new_chunk = DocumentChunk(
        chunk_id="new-chunk",
        document_id="doc",
        document_name="Evidence.pdf",
        page_number=2,
        content="additional document body",
        source_path="data/documents/Evidence.pdf",
        metadata={"document_name": "Evidence.pdf"},
    )

    added = store.add_chunks(
        [existing_chunk, new_chunk],
        [[0.1, 0.2], [0.3, 0.4]],
    )

    assert added == 1
    assert store.collection.rows["existing-chunk"] == "original document body"
    assert store.collection.rows["new-chunk"] == "additional document body"
