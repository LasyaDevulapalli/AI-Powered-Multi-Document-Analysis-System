from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ProcessedPage(BaseModel):
    page_number: int
    text: str
    metadata: Dict[str, Any] = {}

class ExtractedDocument(BaseModel):
    document_id: str
    document_name: str
    source_path: str
    total_pages: int
    pages: List[ProcessedPage]
    error: Optional[str] = None
    is_valid: bool = True

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    content: str
    source_path: str
    metadata: Dict[str, Any] = {}

class BaseDocumentExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> ExtractedDocument:
        """Extract text content and page-level metadata from a document file."""
        pass
