from abc import ABC, abstractmethod
from typing import List
from app.core.config import settings
from app.core.logging_config import logger

class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of document chunk texts."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a user query."""
        pass


class SentenceTransformerEmbeddingService(BaseEmbeddingService):
    """Local high-performance embeddings using sentence-transformers (zero API cost)."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        logger.info(f"Initializing SentenceTransformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text], show_progress_bar=False)
        return embedding[0].tolist()


class GeminiEmbeddingService(BaseEmbeddingService):
    """Google Gemini API Embeddings."""

    def __init__(self, api_key: str = None, model_name: str = "text-embedding-004"):
        from google import genai
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required for GeminiEmbeddingService")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = []
        for text in texts:
            res = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
            )
            embeddings.append(res.embedding.values)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        res = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
        )
        return res.embedding.values


def get_embedding_service(provider: str = None, model_name: str = None) -> BaseEmbeddingService:
    provider = (provider or settings.EMBEDDING_PROVIDER).lower()
    model_name = model_name or settings.EMBEDDING_MODEL_NAME

    if provider in ["sentence-transformers", "local", "hf"]:
        return SentenceTransformerEmbeddingService(model_name=model_name)
    elif provider == "gemini":
        return GeminiEmbeddingService(model_name=model_name)
    else:
        logger.warning(f"Unknown embedding provider '{provider}', falling back to sentence-transformers")
        return SentenceTransformerEmbeddingService(model_name="all-MiniLM-L6-v2")
