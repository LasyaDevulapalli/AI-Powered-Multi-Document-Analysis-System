import os
import urllib.parse
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from app.api.schemas import (
    HealthResponse,
    StatusResponse,
    QueryRequest,
    QueryResponse,
    IndexRequest,
    IndexResponse,
    DocumentLibraryResponse,
)
from app.rag.pipeline import RAGPipeline
from app.core.config import settings
from app.core.logging_config import logger
from app.document_processing.library import (
    list_library_documents,
    resolve_public_document_id,
)

router = APIRouter()

# Global RAG Pipeline instance
pipeline = RAGPipeline()

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return HealthResponse(
        status="ok",
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION
    )

@router.get("/api/status", response_model=StatusResponse, tags=["Knowledge Base"])
def get_kb_status():
    try:
        status_info = pipeline.get_status()
        return StatusResponse(
            is_indexed=status_info["is_indexed"],
            total_chunks=status_info["total_chunks"],
            total_documents=status_info["total_documents"],
            document_names=status_info["document_names"],
            documents_details=status_info.get("documents_details", []),
            domain_title=settings.DOMAIN_TITLE,
            collection_name=status_info["collection_name"]
        )
    except Exception as e:
        logger.error(f"Error fetching KB status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Knowledge Base status."
        )

@router.post("/api/query", response_model=QueryResponse, tags=["QA RAG"])
def answer_user_query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question text cannot be empty."
        )

    try:
        result = pipeline.answer_question(question=request.question, top_k=request.top_k)
        return QueryResponse(**result)
    except RuntimeError as re:
        logger.error(f"LLM Runtime error during query: {str(re)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Provider Error: {str(re)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while retrieving information."
        )

@router.post("/api/analyze", response_model=QueryResponse, tags=["Multi-Doc Analysis"])
def analyze_multi_doc(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis query text cannot be empty."
        )

    try:
        result = pipeline.analyze_multi_document(question=request.question, top_k=request.top_k)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error during multi-document analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-document analysis failed: {str(e)}"
        )

@router.post("/api/index", response_model=IndexResponse, tags=["Knowledge Base"])
def trigger_indexing(request: IndexRequest):
    try:
        result = pipeline.index_documents(force_reindex=request.force_reindex)
        return IndexResponse(**result)
    except Exception as e:
        logger.error(f"Error during document indexing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )

@router.get(
    "/api/library/documents",
    response_model=DocumentLibraryResponse,
    tags=["Documents"],
)
def list_prepared_documents(
    search: Optional[str] = Query(default=None, max_length=200),
    subject: Optional[str] = Query(default=None, max_length=100),
    document_status: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        status_info = pipeline.get_status()
        result = list_library_documents(
            indexed_records=pipeline.vector_store.get_document_records(),
            total_chunks=status_info["total_chunks"],
            search=search,
            subject=subject,
            status=document_status,
            page=page,
            page_size=page_size,
        )
        return DocumentLibraryResponse(**result)
    except Exception as e:
        logger.error("Error listing prepared documents: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prepared document library.",
        )

@router.get("/api/library/documents/{document_id}/pdf", tags=["Documents"])
def get_library_document(
    document_id: str,
    download: bool = Query(default=False),
):
    target_path = resolve_public_document_id(document_id)
    if target_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested prepared document is unavailable.",
        )
    disposition = "attachment" if download else "inline"
    return FileResponse(
        path=str(target_path),
        media_type="application/pdf",
        filename=target_path.name,
        headers={
            "Content-Disposition": f'{disposition}; filename="{target_path.name}"',
            "Accept-Ranges": "bytes",
        },
    )

@router.get("/api/documents/{filename:path}", tags=["Documents"])
@router.get("/documents/{filename:path}", include_in_schema=False)
def get_original_document(
    filename: str,
    source_path: Optional[str] = Query(default=None),
):
    """
    Securely serves original PDF documents from the configured domain documents directory.
    Validates against path traversal and ensures only existing .pdf files can be streamed.
    """
    if not filename or not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document filename is required."
        )

    # Decode URL-encoded characters (e.g. %20 for spaces)
    decoded_filename = urllib.parse.unquote(filename).strip()

    # Reject null bytes or obvious path traversal attempts
    if "\x00" in decoded_filename or ".." in decoded_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document filename. Path traversal is not permitted."
        )

    # Ensure filename matches base name (no directory separators allowed)
    cleaned_name = os.path.basename(decoded_filename)
    if cleaned_name != decoded_filename or "/" in decoded_filename or "\\" in decoded_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document filename. Nested paths are not permitted."
        )

    # Restrict strictly to PDF files
    if not cleaned_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) can be accessed."
        )

    allowed_roots = [
        Path(settings.DOCUMENTS_DIR).resolve(),
        Path(settings.SUBJECT_MATERIALS_DIR).resolve(),
    ]
    target_path = None
    if source_path:
        candidate = Path(source_path).resolve()
        if candidate.name != cleaned_name or not any(
            candidate.is_relative_to(root) for root in allowed_roots
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access denied: Invalid file path."
            )
        if candidate.is_file():
            target_path = candidate
    else:
        matches = []
        for root in allowed_roots:
            if not root.exists():
                continue
            candidate = root / cleaned_name
            if candidate.is_file():
                matches.append(candidate.resolve())
            if root == Path(settings.SUBJECT_MATERIALS_DIR).resolve():
                matches.extend(
                    path.resolve()
                    for path in root.rglob(cleaned_name)
                    if path.is_file()
                )
        matches = list(dict.fromkeys(matches))
        if len(matches) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Multiple documents named '{cleaned_name}' were found. "
                    "Specify the cited source_path."
                )
            )
        if matches:
            target_path = matches[0]

    if target_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{cleaned_name}' was not found in the domain knowledge base."
        )

    logger.info(f"Serving PDF document: {cleaned_name}")
    return FileResponse(
        path=str(target_path),
        media_type="application/pdf",
        filename=cleaned_name,
        headers={
            "Content-Disposition": f'inline; filename="{cleaned_name}"',
            "Accept-Ranges": "bytes"
        }
    )
