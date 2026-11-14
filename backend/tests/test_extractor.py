import os
import pytest
from pathlib import Path
from app.document_processing.pdf_extractor import PDFExtractor

def test_pdf_extractor_valid():
    docs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "documents"
    sample_pdf = docs_dir / "AI_RAG_Architecture_Paper.pdf"
    
    assert sample_pdf.exists(), "Sample PDF must exist for extractor test."
    
    extractor = PDFExtractor()
    extracted = extractor.extract(str(sample_pdf))
    
    assert extracted.is_valid is True
    assert extracted.total_pages >= 1
    assert len(extracted.pages) == extracted.total_pages
    assert "Retrieval-Augmented Generation" in extracted.pages[0].text
    assert extracted.pages[0].metadata["page_number"] == 1
    assert extracted.pages[0].metadata["document_name"] == "AI_RAG_Architecture_Paper.pdf"

def test_pdf_extractor_missing_file():
    extractor = PDFExtractor()
    extracted = extractor.extract("non_existent_file.pdf")
    
    assert extracted.is_valid is False
    assert extracted.total_pages == 0
    assert "does not exist" in extracted.error
