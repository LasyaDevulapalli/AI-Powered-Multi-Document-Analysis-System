from unittest.mock import patch

from app.rag.llm_service import GroqLLMService


def test_grounded_prompt_requires_real_document_and_page_citations():
    service = GroqLLMService(api_key="test-only-key")
    chunks = [
        {
            "document_name": "GATE_2027_CS_Syllabus.pdf",
            "page_number": 12,
            "chunk_id": "syllabus-p12-c3",
            "content": "The evidence passage describes the topic.",
        }
    ]

    try:
        with patch.object(
            service,
            "_call_groq_api",
            return_value="Grounded response.",
        ) as call_api:
            answer = service.generate_grounded_answer(
                "What is the topic?", chunks
            )

        messages = call_api.call_args.args[0]
        assert answer == "Grounded response."
        assert "[Document Name, p. N]" in messages[0]["content"]
        assert "GATE_2027_CS_Syllabus.pdf" in messages[1]["content"]
        assert "Page: 12" in messages[1]["content"]
        assert "Chunk ID: syllabus-p12-c3" in messages[1]["content"]
        assert "Conceptual:" in messages[1]["content"]
    finally:
        service.close()


def test_multi_document_prompt_requests_synthesis_with_per_source_citations():
    service = GroqLLMService(api_key="test-only-key")
    chunks = [
        {
            "document_name": "Doc_A.pdf",
            "page_number": 2,
            "chunk_id": "a-2",
            "content": "Evidence from the first source.",
        },
        {
            "document_name": "Doc_B.pdf",
            "page_number": 8,
            "chunk_id": "b-8",
            "content": "Evidence from the second source.",
        },
    ]

    try:
        with patch.object(
            service,
            "_call_groq_api",
            return_value="Synthesis.",
        ) as call_api:
            answer = service.generate_multi_doc_analysis(
                "Compare the approaches", chunks
            )

        user_prompt = call_api.call_args.args[0][1]["content"]
        assert answer == "Synthesis."
        assert "distinct documents" in user_prompt
        assert "[Document Name, p. N]" in user_prompt
        assert "Doc_A.pdf" in user_prompt and "Page: 2" in user_prompt
        assert "Doc_B.pdf" in user_prompt and "Page: 8" in user_prompt
        assert "Comparison:" in user_prompt
    finally:
        service.close()
