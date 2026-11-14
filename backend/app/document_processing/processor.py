from pathlib import Path
from typing import List, Dict, Type
from app.document_processing.base import BaseDocumentExtractor, ExtractedDocument
from app.document_processing.pdf_extractor import PDFExtractor
from app.core.logging_config import logger
from app.core.config import settings

class DocumentProcessor:
    """Orchestrates document discovery and text extraction across supported formats."""

    def __init__(self):
        self.extractors: Dict[str, BaseDocumentExtractor] = {
            ".pdf": PDFExtractor()
        }
        self.last_scan_summary = {
            "pdfs_discovered": 0,
            "pdfs_extracted": 0,
            "pdfs_skipped": 0,
            "errors": 0,
            "subjects_represented": [],
        }

    def register_extractor(self, extension: str, extractor: BaseDocumentExtractor):
        self.extractors[extension.lower()] = extractor

    def scan_and_extract(self, docs_dir: Path = None) -> List[ExtractedDocument]:
        is_explicit_root = docs_dir is not None
        roots = (
            [Path(docs_dir)]
            if is_explicit_root
            else [
                Path(settings.DOCUMENTS_DIR),
                Path(settings.SUBJECT_MATERIALS_DIR),
            ]
        )
        dataset_root = Path(settings.SUBJECT_MATERIALS_DIR).resolve()
        files = []
        seen_paths = set()
        for root in roots:
            if not root.exists():
                logger.warning(f"Document source directory does not exist: {root}")
                continue
            candidates = root.rglob("*") if root == Path(settings.SUBJECT_MATERIALS_DIR) else root.iterdir()
            for candidate in candidates:
                if not candidate.is_file() or candidate.suffix.lower() not in self.extractors:
                    continue
                resolved = candidate.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                files.append(candidate)

        files.sort(key=lambda path: str(path).lower())
        self.last_scan_summary = {
            "pdfs_discovered": len(files),
            "pdfs_extracted": 0,
            "pdfs_skipped": 0,
            "errors": 0,
            "subjects_represented": [],
        }
        logger.info(
            "Scanning PDF sources %s: found %s PDFs.",
            ", ".join(str(root) for root in roots),
            len(files),
        )

        extracted_docs: List[ExtractedDocument] = []
        for file_path in files:
            ext = file_path.suffix.lower()
            if ext in self.extractors:
                logger.info(f"Processing supported document: {file_path.name}")
                extracted_doc = self.extractors[ext].extract(str(file_path))
                is_dataset_material = (
                    not is_explicit_root
                    and file_path.resolve().is_relative_to(dataset_root)
                )
                if extracted_doc.is_valid and is_dataset_material:
                    extracted_text = "\n".join(
                        page.text for page in extracted_doc.pages
                    ).strip()
                    alpha_ratio = sum(
                        char.isalpha() for char in extracted_text
                    ) / max(len(extracted_text), 1)
                    if (
                        len(extracted_text) < settings.INGEST_MIN_TEXT_CHARACTERS
                        or alpha_ratio < settings.INGEST_MIN_ALPHA_RATIO
                    ):
                        extracted_doc.is_valid = False
                        extracted_doc.error = (
                            "Excluded from searchable ingestion because extracted "
                            f"text quality was below threshold "
                            f"(characters={len(extracted_text)}, "
                            f"alphabetic_ratio={alpha_ratio:.2f})."
                        )
                    else:
                        subject = file_path.parent.name
                        for page in extracted_doc.pages:
                            page.metadata["subject"] = subject

                if extracted_doc.is_valid:
                    self.last_scan_summary["pdfs_extracted"] += 1
                    if is_dataset_material:
                        subject = file_path.parent.name
                        self.last_scan_summary["subjects_represented"].append(
                            subject
                        )
                else:
                    self.last_scan_summary["pdfs_skipped"] += 1
                    if extracted_doc.error and (
                        extracted_doc.error.startswith("Unreadable or corrupted")
                        or "Error parsing PDF" in extracted_doc.error
                    ):
                        self.last_scan_summary["errors"] += 1
                extracted_docs.append(extracted_doc)

        self.last_scan_summary["subjects_represented"] = sorted(
            set(self.last_scan_summary["subjects_represented"])
        )

        return extracted_docs
