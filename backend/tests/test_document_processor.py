from pathlib import Path

from app.core.config import settings
from app.document_processing.base import ExtractedDocument, ProcessedPage
from app.document_processing.processor import DocumentProcessor
from app.rag.chunker import TextChunker


class FixturePdfExtractor:
    def extract(self, file_path):
        path = Path(file_path)
        text = "Readable subject material. " * 30
        if path.name == "short.pdf":
            text = "Short note."
        return ExtractedDocument(
            document_id=path.stem,
            document_name=path.name,
            source_path=str(path.resolve()),
            total_pages=1,
            pages=[
                ProcessedPage(
                    page_number=1,
                    text=text,
                    metadata={"document_name": path.name, "page_number": 1},
                )
            ],
        )


def test_default_scan_recurses_subject_materials_and_excludes_low_quality(
    tmp_path, monkeypatch
):
    documents_dir = tmp_path / "documents"
    subject_root = tmp_path / "subject_materials"
    subject_dir = subject_root / "04_operating_systems"
    documents_dir.mkdir()
    subject_dir.mkdir(parents=True)

    (documents_dir / "existing.pdf").touch()
    readable_path = subject_dir / "readable.pdf"
    readable_path.touch()
    (subject_dir / "short.pdf").touch()

    monkeypatch.setattr(settings, "DOCUMENTS_DIR", documents_dir)
    monkeypatch.setattr(settings, "SUBJECT_MATERIALS_DIR", subject_root)
    processor = DocumentProcessor()
    processor.extractors[".pdf"] = FixturePdfExtractor()

    extracted = processor.scan_and_extract()

    assert [doc.document_name for doc in extracted] == [
        "existing.pdf",
        "readable.pdf",
        "short.pdf",
    ]
    assert all(doc.is_valid for doc in extracted[:2])
    assert not extracted[2].is_valid
    assert processor.last_scan_summary == {
        "pdfs_discovered": 3,
        "pdfs_extracted": 2,
        "pdfs_skipped": 1,
        "errors": 0,
        "subjects_represented": ["04_operating_systems"],
    }

    chunk = TextChunker().chunk_document(extracted[1])[0]
    assert chunk.document_name == "readable.pdf"
    assert chunk.page_number == 1
    assert chunk.source_path == str(readable_path.resolve())
    assert chunk.metadata["subject"] == "04_operating_systems"
