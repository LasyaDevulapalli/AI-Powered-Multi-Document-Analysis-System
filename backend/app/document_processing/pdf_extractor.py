import os
import hashlib
from pathlib import Path
from pypdf import PdfReader
from app.document_processing.base import BaseDocumentExtractor, ExtractedDocument, ProcessedPage
from app.core.config import settings
from app.core.logging_config import logger

class PDFExtractor(BaseDocumentExtractor):
    """Extracts text page-by-page from PDF files with error handling and readability checks."""

    def extract(self, file_path: str) -> ExtractedDocument:
        path = Path(file_path)
        doc_name = path.name
        dataset_root = Path(settings.SUBJECT_MATERIALS_DIR).resolve()
        resolved_path = path.resolve()
        identity = (
            str(resolved_path)
            if dataset_root in resolved_path.parents
            else doc_name
        )
        doc_id = hashlib.md5(identity.encode("utf-8")).hexdigest()[:12]

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return ExtractedDocument(
                document_id=doc_id,
                document_name=doc_name,
                source_path=str(path.resolve()),
                total_pages=0,
                pages=[],
                error=f"File does not exist: {file_path}",
                is_valid=False
            )

        try:
            reader = PdfReader(str(path))
            total_pages = len(reader.pages)
            
            if total_pages == 0:
                return ExtractedDocument(
                    document_id=doc_id,
                    document_name=doc_name,
                    source_path=str(path.resolve()),
                    total_pages=0,
                    pages=[],
                    error="PDF has 0 pages (empty document)",
                    is_valid=False
                )

            pages = []
            total_extracted_text_len = 0

            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                cleaned_text = page_text.strip()
                total_extracted_text_len += len(cleaned_text)

                pages.append(ProcessedPage(
                    page_number=page_num,
                    text=cleaned_text,
                    metadata={
                        "document_id": doc_id,
                        "document_name": doc_name,
                        "page_number": page_num
                    }
                ))

            if total_extracted_text_len == 0:
                logger.warning(f"PDF {doc_name} contains no readable text (may be scanned image/empty).")
                return ExtractedDocument(
                    document_id=doc_id,
                    document_name=doc_name,
                    source_path=str(path.resolve()),
                    total_pages=total_pages,
                    pages=pages,
                    error="PDF contains no extractable text. Scanned images or empty documents are not indexed in Phase 1.",
                    is_valid=False
                )

            logger.info(f"Successfully extracted {len(pages)} pages from {doc_name} ({total_extracted_text_len} chars)")
            return ExtractedDocument(
                document_id=doc_id,
                document_name=doc_name,
                source_path=str(path.resolve()),
                total_pages=total_pages,
                pages=pages,
                error=None,
                is_valid=True
            )

        except Exception as e:
            logger.error(f"Error parsing PDF {doc_name}: {str(e)}")
            return ExtractedDocument(
                document_id=doc_id,
                document_name=doc_name,
                source_path=str(path.resolve()),
                total_pages=0,
                pages=[],
                error=f"Unreadable or corrupted PDF: {str(e)}",
                is_valid=False
            )
