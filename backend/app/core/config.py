
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Multi-Document Analysis System (Phase 1)"
    VERSION: str = "1.0.0"
    DOMAIN_TITLE: str = "Artificial Intelligence & RAG Systems Research Domain"

    BASE_DIR: Path = BACKEND_DIR.parent
    DOCUMENTS_DIR: Path = BASE_DIR / "data" / "documents"
    SUBJECT_MATERIALS_DIR: Path = (
        BASE_DIR / "data" / "datasets" / "gate_cse_phase1" / "subject_materials"
    )
    VECTOR_STORE_DIR: Path = BASE_DIR / "vector_store"
    CHROMA_COLLECTION_NAME: str = "domain_knowledge_base"

    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    TOP_K: int = 8
    INGEST_MIN_TEXT_CHARACTERS: int = 500
    INGEST_MIN_ALPHA_RATIO: float = 0.35
    EMBEDDING_BATCH_SIZE: int = 64

    # Embedding Configuration
    # Options: "sentence-transformers", "gemini", "openai"
    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # LLM Configuration
    # Options: "gemini", "groq", "openai", "mock"
    LLM_PROVIDER: str = "groq"
    LLM_MODEL_NAME: str = "gemini-3.8-flash"
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"

    # API Keys
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure directories exist
settings.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
