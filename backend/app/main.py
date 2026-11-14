import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure app package is importable
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.routes import router
from app.core.config import settings
from app.core.logging_config import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Domain-specific Multi-Document RAG System backend (Phase 1)"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    logger.info(f"--- Starting {settings.PROJECT_NAME} v{settings.VERSION} ---")
    logger.info(f"Documents directory: {settings.DOCUMENTS_DIR.resolve()}")
    logger.info(f"Vector store directory: {settings.VECTOR_STORE_DIR.resolve()}")
    logger.info(f"Embedding Provider: {settings.EMBEDDING_PROVIDER} ({settings.EMBEDDING_MODEL_NAME})")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER} ({settings.LLM_MODEL_NAME})")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
