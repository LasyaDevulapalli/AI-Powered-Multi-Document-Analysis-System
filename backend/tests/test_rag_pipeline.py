from app.rag.llm_service import _question_guidance
from app.rag.pipeline import RAGPipeline
from app.rag.vector_store import VectorStoreManager


class FakeEmbeddingService:
    def embed_query(self, question):
        return [0.0]


class FakeVectorStore:
    MIN_SEMANTIC_SCORE = VectorStoreManager.MIN_SEMANTIC_SCORE
    MIN_KEYWORD_COVERAGE = VectorStoreManager.MIN_KEYWORD_COVERAGE

    def __init__(self, chunks):
        self.chunks = chunks

    def get_status(self):
        return {"is_indexed": True}

    def query(self, *args, **kwargs):
        return self.chunks


class FakeLLMService:
    generation_enabled = True

    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def generate_grounded_answer(self, question, chunks):
        self.calls += 1
        return self.answer


def _pipeline(chunks, llm):
    pipeline = object.__new__(RAGPipeline)
    pipeline.embedding_service = FakeEmbeddingService()
    pipeline.vector_store = FakeVectorStore(chunks)
    pipeline.llm_service = llm
    return pipeline


def _chunk(semantic_score=0.8, keyword_score=0.0):
    return {
        "document_name": "Evidence.pdf",
        "page_number": 3,
        "chunk_id": "chunk-3",
        "score": 0.8,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "content": (
            "Evidence passage with enough substantive text to evaluate its "
            "relevance to the question."
        ),
        "source_path": "data/documents/Evidence.pdf",
    }


def test_grounding_requires_relevant_evidence_and_successful_generation():
    llm = FakeLLMService("Evidence-based answer [Evidence.pdf, p. 3].")
    pipeline = _pipeline([_chunk()], llm)

    result = pipeline.answer_question("Explain the concept", top_k=2)

    assert result["is_grounded"] is True
    assert result["sources"][0]["document_name"] == "Evidence.pdf"
    assert result["sources"][0]["page_number"] == 3
    assert result["sources"][0]["chunk_id"] == "chunk-3"
    assert result["sources"][0]["source_path"] == "data/documents/Evidence.pdf"
    assert result["sources"][0]["document_id"]
    assert result["sources"][0]["hybrid_score"] == 0.8


def test_retrieved_but_insufficient_evidence_does_not_call_llm():
    llm = FakeLLMService("This should not be generated.")
    pipeline = _pipeline([_chunk(semantic_score=0.1)], llm)

    result = pipeline.answer_question("Explain an unrelated concept", top_k=2)

    assert result["is_grounded"] is False
    assert "not have sufficient relevant evidence" in result["answer"]
    assert llm.calls == 0


def test_syllabus_topic_lists_do_not_ground_explanatory_answers():
    llm = FakeLLMService("This should not be generated.")
    pipeline = _pipeline([], llm)
    syllabus_chunk = _chunk()
    syllabus_chunk["document_name"] = "GATE_2027_CS_Syllabus.pdf"
    syllabus_chunk["content"] = (
        "Databases include an ER model, relational model, relational algebra, "
        "tuple calculus, SQL, integrity constraints, normal forms, file "
        "organization, B and B+ tree indexing, transactions, and concurrency "
        "control."
    )

    assert not pipeline._has_sufficient_evidence(
        [syllabus_chunk],
        "Explain database normalization, SQL transactions, and B+ tree indexing.",
    )
    assert pipeline._has_sufficient_evidence(
        [syllabus_chunk],
        "Which database topics are listed in the GATE syllabus?",
    )


def test_past_question_papers_do_not_ground_explanatory_answers():
    llm = FakeLLMService("This should not be generated.")
    pipeline = _pipeline([], llm)
    question_paper_chunk = _chunk()
    question_paper_chunk["document_name"] = "GATE_CSE_2026_AN_Question_Paper.pdf"

    assert not pipeline._has_sufficient_evidence(
        [question_paper_chunk],
        "Explain database normalization and transaction isolation.",
    )


def test_successful_text_from_unconfigured_llm_is_not_marked_grounded():
    llm = FakeLLMService("LLM provider is not configured.")
    llm.generation_enabled = False
    pipeline = _pipeline([_chunk()], llm)

    result = pipeline.answer_question("Explain the concept", top_k=2)

    assert result["is_grounded"] is False


def test_force_reindex_refuses_to_mutate_the_active_collection():
    class ProtectedVectorStore:
        def clear_collection(self):
            raise AssertionError("The active collection must not be cleared")

    class UnusedProcessor:
        def scan_and_extract(self):
            raise AssertionError("A refused re-index must not start scanning")

    pipeline = object.__new__(RAGPipeline)
    pipeline.vector_store = ProtectedVectorStore()
    pipeline.processor = UnusedProcessor()

    result = pipeline.index_documents(force_reindex=True)

    assert result["status"] == "warning"
    assert "separately named collection" in result["message"]


def test_question_guidance_selects_conceptual_numeric_algorithmic_and_comparison_modes():
    assert "Conceptual:" in _question_guidance("What is deadlock?")
    assert "Numerical:" in _question_guidance("Calculate the value for 2 processes")
    assert "Algorithmic:" in _question_guidance("Explain the algorithm steps")
    assert "Comparison:" in _question_guidance("Compare the two approaches")


def test_generated_answer_with_unknown_citation_is_withheld():
    llm = FakeLLMService("Result [Invented.pdf, p. 99].")
    pipeline = _pipeline([_chunk()], llm)

    result = pipeline.answer_question("Explain the concept", top_k=2)

    assert result["is_grounded"] is False
    assert "was withheld" in result["answer"]


def test_generated_answer_with_inconsistent_arithmetic_is_withheld():
    llm = FakeLLMService(
        "The ratio is 0.5 / 0.20 = 4 [Evidence.pdf, p. 3]."
    )
    pipeline = _pipeline([_chunk()], llm)

    result = pipeline.answer_question("Calculate the ratio", top_k=2)

    assert result["is_grounded"] is False
    assert "was withheld" in result["answer"]


def test_query_decomposition_retrieves_evidence_for_each_explicit_part():
    class ComponentEmbedding:
        def __init__(self):
            self.queries = []

        def embed_query(self, question):
            self.queries.append(question)
            return [float(len(self.queries))]

    class ComponentVectorStore(FakeVectorStore):
        def __init__(self):
            self.questions = []

        def query(self, query_vector, top_k, question, diversify_documents=False):
            self.questions.append(question)
            name = "Cache.pdf" if "cache" in question.lower() else "AMAT.pdf"
            chunk_id = f"{name}-{len(self.questions)}"
            return [
                {
                    "document_name": name,
                    "page_number": 2,
                    "chunk_id": chunk_id,
                    "score": 0.8,
                    "semantic_score": 0.7,
                    "keyword_score": 0.6,
                    "content": f"Evidence about {question} with enough detail.",
                    "source_path": f"data/documents/{name}",
                }
            ]

    pipeline = object.__new__(RAGPipeline)
    pipeline.embedding_service = ComponentEmbedding()
    pipeline.vector_store = ComponentVectorStore()
    question = "Explain cache mapping; calculate AMAT from the hit ratio."

    chunks = pipeline._retrieve_evidence(
        question,
        top_k=4,
        diversify_documents=False,
    )

    assert any("cache mapping" in item.lower() for item in pipeline.vector_store.questions)
    assert any("calculate AMAT" in item for item in pipeline.vector_store.questions)
    assert {chunk["document_name"] for chunk in chunks} == {
        "Cache.pdf",
        "AMAT.pdf",
    }


def test_cache_mapping_comparison_retrieves_each_mapping_mode():
    question = (
        "Explain direct mapping, fully associative mapping, and set-associative "
        "mapping in cache memory. Compare their advantages and disadvantages."
    )
    expected_documents = {
        "MIT_COA_L07_Memory_Hierarchy.pdf",
        "GATE_CSE_2026_FN_Question_Paper.pdf",
    }

    class CacheMappingVectorStore(FakeVectorStore):
        def query(self, query_vector, top_k, question, diversify_documents=False):
            query_lower = question.lower()
            if "direct mapped cache" in query_lower:
                document_name, page_number = (
                    "MIT_COA_L07_Memory_Hierarchy.pdf",
                    22,
                )
            elif "fully associative cache" in query_lower:
                document_name, page_number = (
                    "MIT_COA_L07_Memory_Hierarchy.pdf",
                    25,
                )
            elif "set associative cache" in query_lower:
                document_name, page_number = (
                    "GATE_CSE_2026_FN_Question_Paper.pdf",
                    27,
                )
            else:
                document_name, page_number = "Digital_Logic_Memories.pdf", 18

            return [
                {
                    "document_name": document_name,
                    "page_number": page_number,
                    "chunk_id": f"{document_name}-p{page_number}",
                    "score": 0.8,
                    "semantic_score": 0.6,
                    "keyword_score": 0.5,
                    "content": f"Cache mapping evidence for {question}.",
                    "source_path": f"data/documents/{document_name}",
                }
            ]

    class CacheMappingEmbedding(FakeEmbeddingService):
        def __init__(self):
            self.queries = []

        def embed_query(self, question):
            self.queries.append(question)
            return [0.0]

    pipeline = object.__new__(RAGPipeline)
    pipeline.embedding_service = CacheMappingEmbedding()
    pipeline.vector_store = CacheMappingVectorStore([])

    chunks = pipeline._retrieve_evidence(
        question,
        top_k=4,
        diversify_documents=False,
    )

    assert pipeline.embedding_service.queries == [
        question,
        "direct mapped cache",
        "fully associative cache",
        "set associative cache",
    ]
    assert {chunk["page_number"] for chunk in chunks} == {18, 22, 25, 27}
    assert expected_documents.issubset(
        {chunk["document_name"] for chunk in chunks}
    )
