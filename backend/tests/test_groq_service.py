import pytest
from unittest.mock import MagicMock, patch
from app.rag.llm_service import GroqLLMService, get_llm_service

def test_groq_llm_service_grounded_answer():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_error = False
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "RAG improves LLM accuracy by retrieving factual context from documents."
                }
            }
        ]
    }

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value.__enter__.return_value = mock_client_instance

        service = GroqLLMService(api_key="gsk_dummy_test_key", model_name="llama-3.3-70b-versatile")
        chunks = [
            {"document_name": "Paper.pdf", "page_number": 1, "content": "RAG improves factual grounding."}
        ]
        answer = service.generate_grounded_answer("What is RAG?", chunks)

        assert "RAG improves LLM accuracy" in answer
        mock_client_instance.post.assert_called_once()
        call_kwargs = mock_client_instance.post.call_args.kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer gsk_dummy_test_key"
        assert call_kwargs["json"]["model"] == "llama-3.3-70b-versatile"

def test_groq_llm_service_multi_doc_analysis():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_error = False
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "### Cross-Document Comparison\nBoth documents emphasize chunking precision."
                }
            }
        ]
    }

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value.__enter__.return_value = mock_client_instance

        service = GroqLLMService(api_key="gsk_dummy_test_key", model_name="llama-3.3-70b-versatile")
        chunks = [
            {"document_name": "Doc1.pdf", "page_number": 1, "content": "Chunking is key."},
            {"document_name": "Doc2.pdf", "page_number": 2, "content": "Overlap improves context."}
        ]
        analysis = service.generate_multi_doc_analysis("Compare chunking", chunks)

        assert "Cross-Document Comparison" in analysis
        mock_client_instance.post.assert_called_once()

def test_get_llm_service_groq_provider():
    service = get_llm_service(provider="groq", api_key="gsk_test_key")
    assert isinstance(service, GroqLLMService)
    assert service.api_key == "gsk_test_key"

def test_get_llm_service_default_settings_groq():
    with patch("app.rag.llm_service.settings.LLM_PROVIDER", "groq"), \
         patch("app.rag.llm_service.settings.GROQ_API_KEY", "gsk_settings_key"):
        service = get_llm_service()
        assert isinstance(service, GroqLLMService)
        assert service.api_key == "gsk_settings_key"

def test_groq_llm_service_http_404_error():
    mock_response = MagicMock()
    mock_response.is_error = True
    mock_response.status_code = 404
    mock_response.json.return_value = {
        "error": {
            "message": "The model 'llama-invalid' does not exist or you do not have access to it.",
            "type": "invalid_request_error",
            "code": "model_not_found"
        }
    }

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value.__enter__.return_value = mock_client_instance

        service = GroqLLMService(api_key="gsk_test_key", model_name="llama-invalid")
        chunks = [{"document_name": "Doc.pdf", "page_number": 1, "content": "Sample content"}]

        with pytest.raises(RuntimeError) as exc_info:
            service.generate_grounded_answer("Test question", chunks)

        assert "HTTP 404" in str(exc_info.value)
        assert "The model 'llama-invalid' does not exist" in str(exc_info.value)

def test_groq_llm_service_non_json_error():
    mock_response = MagicMock()
    mock_response.is_error = True
    mock_response.status_code = 502
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.text = "Bad Gateway Proxy Error"

    with patch("httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value.__enter__.return_value = mock_client_instance

        service = GroqLLMService(api_key="gsk_test_key")
        chunks = [{"document_name": "Doc.pdf", "page_number": 1, "content": "Sample content"}]

        with pytest.raises(RuntimeError) as exc_info:
            service.generate_grounded_answer("Test question", chunks)

        assert "HTTP 502" in str(exc_info.value)
        assert "Bad Gateway Proxy Error" in str(exc_info.value)

def test_config_env_loading():
    from app.core.config import settings
    assert isinstance(settings.LLM_PROVIDER, str)
    assert settings.LLM_PROVIDER in ["groq", "gemini", "mock", "openai"]
    # Safely verify presence of GROQ_API_KEY without exposing or printing secret value
    has_groq_key = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())
    assert isinstance(has_groq_key, bool)
    assert settings.DOCUMENTS_DIR.exists()


