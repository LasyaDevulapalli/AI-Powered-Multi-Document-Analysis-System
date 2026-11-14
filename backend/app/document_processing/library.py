import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.core.config import settings
from app.document_processing import DocumentProcessor


def public_document_id(source_path: str) -> str:
    """Create an opaque, stable identifier without exposing a filesystem path."""
    normalized_path = str(Path(source_path).resolve()).casefold()
    return hashlib.sha256(normalized_path.encode("utf-8")).hexdigest()[:24]


def _source_paths() -> Iterable[Path]:
    roots = (
        (Path(settings.DOCUMENTS_DIR), False),
        (Path(settings.SUBJECT_MATERIALS_DIR), True),
    )
    seen = set()
    for root, recursive in roots:
        if not root.exists():
            continue
        candidates = root.rglob("*") if recursive else root.iterdir()
        for path in candidates:
            if not path.is_file() or path.suffix.casefold() != ".pdf":
                continue
            resolved = path.resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                continue
            if resolved not in seen:
                seen.add(resolved)
                yield resolved


def _scan_signature() -> tuple:
    signature = []
    for path in _source_paths():
        try:
            stat = path.stat()
        except OSError:
            continue
        signature.append((str(path), stat.st_size, stat.st_mtime_ns))
    return tuple(sorted(signature))


@lru_cache(maxsize=1)
def _extract_repository(signature: tuple):
    # Extraction is cached until a PDF is added, removed, or modified.
    return tuple(DocumentProcessor().scan_and_extract())


def _subject_label(source_path: str, indexed: Optional[Dict[str, Any]]) -> str:
    if indexed and indexed.get("subject"):
        raw_subject = str(indexed["subject"])
    else:
        raw_subject = Path(source_path).parent.name
    raw_subject = re.sub(r"^\d+[_-]*", "", raw_subject)
    if not raw_subject:
        return "Prepared Documents"
    return raw_subject.replace("_", " ").replace("-", " ").title()


def _index_records_by_path(
    indexed_records: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    result = {}
    for record in indexed_records:
        source_path = record.get("source_path")
        if not source_path:
            continue
        result[str(Path(source_path).resolve()).casefold()] = record
    return result


def _status_for_document(is_indexed: bool, is_valid: bool, error: Optional[str]) -> str:
    if is_indexed:
        return "indexed"
    if is_valid:
        return "available_not_indexed"
    if error and "quality" in error.lower():
        return "skipped_quality"
    return "failed_extraction"


def list_library_documents(
    indexed_records: List[Dict[str, Any]],
    total_chunks: int,
    search: Optional[str] = None,
    subject: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    scanned_documents = _extract_repository(_scan_signature())
    indexed_by_path = _index_records_by_path(indexed_records)
    seen_paths = set()
    documents = []

    for extracted in scanned_documents:
        resolved_path = str(Path(extracted.source_path).resolve())
        key = resolved_path.casefold()
        seen_paths.add(key)
        indexed = indexed_by_path.pop(key, None)
        file_available = Path(resolved_path).is_file()
        document_status = _status_for_document(
            indexed is not None, extracted.is_valid, extracted.error
        )
        metadata = (
            indexed.get("metadata", {})
            if indexed
            else (extracted.pages[0].metadata if extracted.pages else {})
        )
        searchable_text = " ".join(
            item.text for item in extracted.pages if item.text
        )
        documents.append(
            {
                "document_id": public_document_id(resolved_path),
                "document_name": Path(resolved_path).stem,
                "subject": _subject_label(resolved_path, metadata),
                "original_filename": Path(resolved_path).name,
                "page_count": extracted.total_pages,
                "indexed_status": document_status,
                "chunk_count": int(indexed.get("chunk_count", 0)) if indexed else 0,
                "available_pdf": file_available,
                "_search_text": searchable_text,
            }
        )

    for record in indexed_by_path.values():
        source_path = record.get("source_path") or ""
        document_name = str(record.get("document_name") or "Unknown document")
        documents.append(
            {
                "document_id": public_document_id(source_path or document_name),
                "document_name": Path(document_name).stem,
                "subject": str(record.get("subject") or "Unknown"),
                "original_filename": Path(document_name).name,
                "page_count": int(record.get("page_count", 0)),
                "indexed_status": "missing_source",
                "chunk_count": int(record.get("chunk_count", 0)),
                "available_pdf": False,
                "_search_text": "",
            }
        )

    documents.sort(
        key=lambda item: (
            item["subject"].casefold(),
            item["document_name"].casefold(),
        )
    )
    status_counts = {}
    for document in documents:
        current_status = document["indexed_status"]
        status_counts[current_status] = status_counts.get(current_status, 0) + 1

    filtered = documents
    if subject:
        filtered = [
            item for item in filtered
            if item["subject"].casefold() == subject.casefold()
        ]
    if status:
        filtered = [
            item for item in filtered
            if item["indexed_status"] == status
        ]
    if search:
        terms = [
            term.casefold()
            for term in re.findall(r"[a-zA-Z0-9]+", search)
            if len(term) > 1
        ]
        if terms:
            filtered = [
                item for item in filtered
                if all(
                    term in " ".join(
                        (
                            item["document_name"],
                            item["original_filename"],
                            item["subject"],
                            item["_search_text"],
                        )
                    ).casefold()
                    for term in terms
                )
            ]

    total = len(filtered)
    start = (page - 1) * page_size
    items = [
        {key: value for key, value in item.items() if not key.startswith("_")}
        for item in filtered[start : start + page_size]
    ]
    return {
        "total_documents": len(documents),
        "indexed_documents": status_counts.get("indexed", 0),
        "total_chunks": total_chunks,
        "status_counts": status_counts,
        "subjects": sorted({item["subject"] for item in documents}, key=str.casefold),
        "documents": items,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "filtered_total": total,
    }


def resolve_public_document_id(document_id: str) -> Optional[Path]:
    if not re.fullmatch(r"[a-f0-9]{24}", document_id):
        return None
    for source_path in _source_paths():
        if public_document_id(str(source_path)) == document_id:
            return source_path
    return None
