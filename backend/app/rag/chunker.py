from typing import List
from app.document_processing.base import ExtractedDocument, DocumentChunk
from app.core.config import settings
from app.core.logging_config import logger

class TextChunker:
    """Splits document text into overlapping chunks while preserving rich document & page metadata."""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_document(self, doc: ExtractedDocument) -> List[DocumentChunk]:
        if not doc.is_valid or not doc.pages:
            logger.warning(f"Skipping chunking for invalid document: {doc.document_name}")
            return []

        chunks: List[DocumentChunk] = []
        chunk_counter = 0

        for page in doc.pages:
            text = page.text
            if not text:
                continue

            # Basic recursive text splitter approach by paragraphs/sentences/spaces
            page_chunks_text = self._split_text(text)

            for idx, c_text in enumerate(page_chunks_text):
                chunk_id = f"{doc.document_id}_p{page.page_number}_c{chunk_counter}"
                chunk_counter += 1

                metadata = {
                    "document_id": doc.document_id,
                    "document_name": doc.document_name,
                    "page_number": page.page_number,
                    "chunk_id": chunk_id,
                    "source_path": doc.source_path,
                    "char_length": len(c_text),
                }
                subject = page.metadata.get("subject")
                if subject:
                    metadata["subject"] = subject

                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    document_name=doc.document_name,
                    page_number=page.page_number,
                    content=c_text,
                    source_path=doc.source_path,
                    metadata=metadata,
                )
                chunks.append(chunk)

        logger.info(f"Generated {len(chunks)} chunks from {doc.document_name} ({doc.total_pages} pages)")
        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Splits a single block of text into chunks with defined overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            
            if end >= text_len:
                chunk_text = text[start:].strip()
                if chunk_text:
                    chunks.append(chunk_text)
                break

            # Try to break at a natural boundary (newline or period or space)
            break_pos = text.rfind('\n', start, end)
            if break_pos == -1 or break_pos < start + (self.chunk_size // 2):
                break_pos = text.rfind('. ', start, end)
            if break_pos == -1 or break_pos < start + (self.chunk_size // 2):
                break_pos = text.rfind(' ', start, end)

            if break_pos != -1 and break_pos > start:
                actual_end = break_pos + 1
            else:
                actual_end = end

            chunk_text = text[start:actual_end].strip()
            if chunk_text:
                chunks.append(chunk_text)

            # Move start forward with overlap
            start = actual_end - self.chunk_overlap
            if start < 0 or start >= actual_end:
                start = actual_end

        return chunks
