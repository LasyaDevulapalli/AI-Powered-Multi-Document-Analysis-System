from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "ok"
    project_name: str
    version: str

class SourceReference(BaseModel):
    document_name: str
    document_id: Optional[str] = None
    page_number: Optional[int] = 1
    chunk_id: str
    hybrid_score: Optional[float] = None
    relevance_score: float
    snippet: str
    source_path: str

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language user question")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of context chunks to retrieve")

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceReference]
    documents_considered: Optional[List[str]] = []
    retrieved_count: int
    elapsed_time: float
    is_grounded: bool

class IndexRequest(BaseModel):
    force_reindex: bool = False

class DocumentDetail(BaseModel):
    document_name: str
    document_id: Optional[str] = None
    subject: Optional[str] = None
    pages: int
    chunks: int
    status: str
    error: Optional[str] = None

class IndexResponse(BaseModel):
    status: str
    message: str
    total_documents: int
    valid_documents: int
    failed_documents: int
    total_chunks: int
    elapsed_time: float
    details: List[DocumentDetail]
    pdfs_discovered: Optional[int] = None
    pdfs_extracted: Optional[int] = None
    pdfs_skipped: Optional[int] = None
    chunks_generated: Optional[int] = None
    chunks_indexed: Optional[int] = None
    subjects_represented: List[str] = Field(default_factory=list)
    errors: Optional[int] = None

class StatusResponse(BaseModel):
    is_indexed: bool
    total_chunks: int
    total_documents: int
    document_names: List[str]
    documents_details: Optional[List[DocumentDetail]] = []
    domain_title: str
    collection_name: str

class LibraryDocument(BaseModel):
    document_id: str
    document_name: str
    subject: str
    original_filename: str
    page_count: int
    indexed_status: str
    chunk_count: int
    available_pdf: bool

class DocumentLibraryResponse(BaseModel):
    total_documents: int
    indexed_documents: int
    total_chunks: int
    status_counts: Dict[str, int]
    subjects: List[str]
    documents: List[LibraryDocument]
    page: int
    page_size: int
    total_pages: int
    filtered_total: int
