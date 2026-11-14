
import time
import math
from typing import List, Dict, Any, Optional

from app.document_processing import DocumentProcessor, DocumentChunk
from app.document_processing.library import public_document_id
from app.rag.answer_validation import verify_generated_answer
from app.rag.query_analysis import decompose_question
from app.rag.chunker import TextChunker
from app.rag.embeddings import get_embedding_service, BaseEmbeddingService
from app.rag.vector_store import VectorStoreManager
from app.rag.llm_service import get_llm_service, BaseLLMService
from app.core.config import settings
from app.core.logging_config import logger


class RAGPipeline:
    """Core RAG Orchestrator for Multi-Document QA and Indexing."""

    def __init__(
        self,
        embedding_service: Optional[BaseEmbeddingService] = None,
        llm_service: Optional[BaseLLMService] = None,
        vector_store: Optional[VectorStoreManager] = None,
    ):
        self.processor = DocumentProcessor()
        self.chunker = TextChunker()
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or VectorStoreManager()
        self.llm_service = llm_service or get_llm_service()

    def index_documents(self, force_reindex: bool = False) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("--- STARTING DOCUMENT INDEXING WORKFLOW ---")

        if force_reindex:
            message = (
                "Force re-indexing was refused to protect the existing ChromaDB "
                "collection. Back up the vector store and use a separately named "
                "collection before rebuilding."
            )
            logger.warning(message)
            return {
                "status": "warning",
                "message": message,
                "total_documents": 0,
                "valid_documents": 0,
                "failed_documents": 0,
                "total_chunks": 0,
                "pdfs_discovered": 0,
                "pdfs_extracted": 0,
                "pdfs_skipped": 0,
                "chunks_generated": 0,
                "chunks_indexed": 0,
                "subjects_represented": [],
                "errors": 0,
                "elapsed_time": round(time.time() - start_time, 2),
                "details": [],
            }

        extracted_docs = self.processor.scan_and_extract()
        scan_summary = getattr(
            self.processor,
            "last_scan_summary",
            {
                "pdfs_discovered": len(extracted_docs),
                "pdfs_extracted": sum(doc.is_valid for doc in extracted_docs),
                "pdfs_skipped": sum(not doc.is_valid for doc in extracted_docs),
                "errors": 0,
                "subjects_represented": [],
            },
        )

        if not extracted_docs:
            logger.warning("No documents found in documents directory.")
            return {
                "status": "warning",
                "message": "No documents found to index.",
                "total_documents": 0,
                "valid_documents": 0,
                "failed_documents": 0,
                "total_chunks": 0,
                "pdfs_discovered": scan_summary["pdfs_discovered"],
                "pdfs_extracted": scan_summary["pdfs_extracted"],
                "pdfs_skipped": scan_summary["pdfs_skipped"],
                "chunks_generated": 0,
                "chunks_indexed": 0,
                "subjects_represented": scan_summary["subjects_represented"],
                "errors": scan_summary["errors"],
                "elapsed_time": round(time.time() - start_time, 2),
                "details": [],
            }

        valid_docs = [d for d in extracted_docs if d.is_valid]
        failed_docs = [d for d in extracted_docs if not d.is_valid]

        all_chunks: List[DocumentChunk] = []
        doc_details = []

        for doc in extracted_docs:
            if doc.is_valid:
                doc_chunks = self.chunker.chunk_document(doc)
                all_chunks.extend(doc_chunks)

                doc_details.append(
                    {
                        "document_name": doc.document_name,
                        "pages": doc.total_pages,
                        "chunks": len(doc_chunks),
                        "status": "success",
                        "error": None,
                    }
                )
            else:
                doc_details.append(
                    {
                        "document_name": doc.document_name,
                        "pages": doc.total_pages,
                        "chunks": 0,
                        "status": "failed",
                        "error": doc.error,
                    }
                )

        if not all_chunks:
            logger.warning(
                "No valid text chunks generated from available documents."
            )
            return {
                "status": "warning",
                "message": "No valid text chunks extracted from documents.",
                "total_documents": len(extracted_docs),
                "valid_documents": len(valid_docs),
                "failed_documents": len(failed_docs),
                "total_chunks": 0,
                "pdfs_discovered": scan_summary["pdfs_discovered"],
                "pdfs_extracted": scan_summary["pdfs_extracted"],
                "pdfs_skipped": scan_summary["pdfs_skipped"],
                "chunks_generated": 0,
                "chunks_indexed": 0,
                "subjects_represented": scan_summary["subjects_represented"],
                "errors": scan_summary["errors"],
                "elapsed_time": round(time.time() - start_time, 2),
                "details": doc_details,
            }

        # Generate embeddings
        chunk_texts = [c.content for c in all_chunks]
        logger.info(
            f"Generating embeddings for {len(all_chunks)} text chunks..."
        )
        batch_size = max(1, settings.EMBEDDING_BATCH_SIZE)
        added_count = 0
        for start in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[start : start + batch_size]
            batch_texts = chunk_texts[start : start + batch_size]
            embeddings = self.embedding_service.embed_documents(batch_texts)
            if len(embeddings) != len(batch_chunks):
                raise RuntimeError(
                    "Embedding service returned a different number of vectors "
                    f"({len(embeddings)}) than chunks ({len(batch_chunks)})."
                )
            added_count += self.vector_store.add_chunks(
                batch_chunks, embeddings
            )
        elapsed = round(time.time() - start_time, 2)

        logger.info(
            f"--- INDEXING COMPLETE: {added_count} chunks indexed in {elapsed}s ---"
        )

        return {
            "status": "success",
            "message": (
                f"Processed {len(valid_docs)} valid documents and added "
                f"{added_count} new chunks. Existing chunk records were not replaced."
            ),
            "total_documents": len(extracted_docs),
            "valid_documents": len(valid_docs),
            "failed_documents": len(failed_docs),
            "total_chunks": added_count,
            "pdfs_discovered": scan_summary["pdfs_discovered"],
            "pdfs_extracted": scan_summary["pdfs_extracted"],
            "pdfs_skipped": scan_summary["pdfs_skipped"],
            "chunks_generated": len(all_chunks),
            "chunks_indexed": added_count,
            "subjects_represented": scan_summary["subjects_represented"],
            "errors": scan_summary["errors"],
            "elapsed_time": elapsed,
            "details": doc_details,
        }

    def answer_question(
        self, question: str, top_k: int = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Received query: '{question}'")

        if not question or not question.strip():
            return {
                "question": question,
                "answer": "Question cannot be empty.",
                "sources": [],
                "retrieved_count": 0,
                "elapsed_time": 0.0,
                "is_grounded": False,
            }

        kb_status = self.vector_store.get_status()

        if not kb_status["is_indexed"]:
            return {
                "question": question,
                "answer": (
                    "The Knowledge Base is currently empty. Please ensure "
                    "domain documents are placed in data/documents and "
                    "indexed before asking questions."
                ),
                "sources": [],
                "retrieved_count": 0,
                "elapsed_time": round(time.time() - start_time, 2),
                "is_grounded": False,
            }

        k = top_k or settings.TOP_K
        retrieved_chunks = self._retrieve_evidence(
            question,
            top_k=k,
            diversify_documents=False,
        )

        if not self._has_sufficient_evidence(retrieved_chunks, question):
            return {
                "question": question,
                "answer": (
                    "Based on the prepared domain documents, I do not have "
                    "sufficient relevant evidence to answer this question."
                ),
                "sources": self._format_sources(retrieved_chunks),
                "documents_considered": list(
                    dict.fromkeys(
                        chunk["document_name"] for chunk in retrieved_chunks
                    )
                ),
                "retrieved_count": len(retrieved_chunks),
                "elapsed_time": round(time.time() - start_time, 2),
                "is_grounded": False,
            }

        # 3. Generate a grounded LLM response
        generation_succeeded = False
        try:
            answer = self.llm_service.generate_grounded_answer(
                question, retrieved_chunks
            )
            generation_succeeded = bool(answer and answer.strip()) and getattr(
                self.llm_service, "generation_enabled", True
            )
            if not answer or not answer.strip():
                answer = (
                    "The answer provider returned no response. "
                    "The retrieved evidence is available below."
                )
            elif generation_succeeded:
                answer_verified, verification_errors = verify_generated_answer(
                    answer, retrieved_chunks
                )
                generation_succeeded = answer_verified
                if not answer_verified:
                    logger.warning(
                        "Generated answer failed source/calculation verification: %s",
                        "; ".join(verification_errors),
                    )
                    answer = (
                        "The generated answer was withheld because its source "
                        "citations or an explicit calculation could not be "
                        "verified against the retrieved evidence. Please review "
                        "the evidence passages below."
                    )
        except Exception as e:
            logger.error(f"LLM Generation Failed: {str(e)}")

            answer = (
                "LLM answer generation failed.\n\n"
                "The system retrieved context blocks, but the LLM provider "
                "encountered an error while generating the answer. "
                "Please check your configured LLM provider and API key. "
                "The retrieved evidence passages are preserved below."
            )

        # 4. Format source references and unique document list
        sources = self._format_sources(retrieved_chunks)
        document_names = list(
            dict.fromkeys(chunk["document_name"] for chunk in retrieved_chunks)
        )
        is_grounded = (
            self._has_sufficient_evidence(retrieved_chunks, question)
            and generation_succeeded
        )

        elapsed = round(time.time() - start_time, 2)

        logger.info(
            f"Query completed in {elapsed}s with {len(sources)} supporting "
            f"sources across {len(document_names)} documents."
        )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "documents_considered": document_names,
            "retrieved_count": len(sources),
            "elapsed_time": elapsed,
            "is_grounded": is_grounded,
        }

    def analyze_multi_document(
        self, question: str, top_k: int = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(
            f"Received multi-doc analysis query: '{question}'"
        )

        if not question or not question.strip():
            return {
                "question": question,
                "answer": "Analysis query cannot be empty.",
                "sources": [],
                "documents_considered": [],
                "retrieved_count": 0,
                "elapsed_time": 0.0,
                "is_grounded": False,
            }

        kb_status = self.vector_store.get_status()

        if not kb_status["is_indexed"]:
            return {
                "question": question,
                "answer": (
                    "The Knowledge Base is currently empty. "
                    "Please index domain documents first."
                ),
                "sources": [],
                "documents_considered": [],
                "retrieved_count": 0,
                "elapsed_time": round(time.time() - start_time, 2),
                "is_grounded": False,
            }

        k = top_k or max(6, settings.TOP_K)
        retrieved_chunks = self._retrieve_evidence(
            question,
            top_k=k,
            diversify_documents=True,
        )

        if not self._has_sufficient_evidence(retrieved_chunks, question):
            return {
                "question": question,
                "answer": (
                    "Based on the prepared domain documents, I do not have "
                    "sufficient relevant evidence to perform this analysis."
                ),
                "sources": self._format_sources(retrieved_chunks),
                "documents_considered": list(
                    dict.fromkeys(
                        chunk["document_name"] for chunk in retrieved_chunks
                    )
                ),
                "retrieved_count": len(retrieved_chunks),
                "elapsed_time": round(time.time() - start_time, 2),
                "is_grounded": False,
            }

        generation_succeeded = False
        try:
            answer = self.llm_service.generate_multi_doc_analysis(
                question, retrieved_chunks
            )
            generation_succeeded = bool(answer and answer.strip()) and getattr(
                self.llm_service, "generation_enabled", True
            )
            if not answer or not answer.strip():
                answer = (
                    "The answer provider returned no response. "
                    "The retrieved evidence is available below."
                )
            elif generation_succeeded:
                answer_verified, verification_errors = verify_generated_answer(
                    answer, retrieved_chunks
                )
                generation_succeeded = answer_verified
                if not answer_verified:
                    logger.warning(
                        "Multi-document answer failed source/calculation "
                        "verification: %s",
                        "; ".join(verification_errors),
                    )
                    answer = (
                        "The generated analysis was withheld because its source "
                        "citations or an explicit calculation could not be "
                        "verified against the retrieved evidence. Please review "
                        "the evidence passages below."
                    )
        except Exception as e:
            logger.error(
                f"LLM Multi-Document Analysis Failed: {str(e)}"
            )

            answer = (
                "LLM multi-document synthesis failed.\n\n"
                "The system retrieved context blocks, but the LLM provider "
                "encountered an error during synthesis. "
                "Please check your configured LLM provider and API key. "
                "The retrieved evidence passages are preserved below."
            )

        # Format source references
        sources = self._format_sources(retrieved_chunks)
        document_names = list(
            dict.fromkeys(chunk["document_name"] for chunk in retrieved_chunks)
        )
        is_grounded = (
            self._has_sufficient_evidence(retrieved_chunks, question)
            and generation_succeeded
        )

        elapsed = round(time.time() - start_time, 2)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "documents_considered": document_names,
            "retrieved_count": len(sources),
            "elapsed_time": elapsed,
            "is_grounded": is_grounded,
        }

    def _retrieve_evidence(
        self,
        question: str,
        top_k: int,
        diversify_documents: bool,
    ) -> List[Dict[str, Any]]:
        components = decompose_question(question)
        if len(components) <= 1:
            query_vector = self.embedding_service.embed_query(question)
            return self.vector_store.query(
                query_vector,
                top_k=top_k,
                question=question,
                diversify_documents=diversify_documents,
            )

        per_component_k = max(2, math.ceil(top_k / len(components)))
        candidates: Dict[str, Dict[str, Any]] = {}
        component_best = []
        for component in components:
            query_vector = self.embedding_service.embed_query(component)
            component_results = self.vector_store.query(
                query_vector,
                top_k=per_component_k,
                question=component,
                diversify_documents=diversify_documents,
            )
            best_chunk_id = None
            for rank, result in enumerate(component_results, start=1):
                chunk_id = result.get("chunk_id") or (
                    result.get("document_name"),
                    result.get("page_number"),
                    result.get("content"),
                )
                key = str(chunk_id)
                candidate = candidates.get(key)
                if candidate is None:
                    candidate = dict(result)
                    candidate["matched_query_components"] = []
                    candidate["_query_fusion_score"] = 0.0
                    candidates[key] = candidate
                candidate["_query_fusion_score"] += 1.0 / (
                    VectorStoreManager.RRF_CONSTANT + rank
                )
                candidate["matched_query_components"].append(component)
                candidate["score"] = max(
                    float(candidate.get("score", 0.0)),
                    float(result.get("score", 0.0)),
                )
                candidate["semantic_score"] = max(
                    float(candidate.get("semantic_score", 0.0)),
                    float(result.get("semantic_score", 0.0)),
                )
                candidate["keyword_score"] = max(
                    float(candidate.get("keyword_score", 0.0)),
                    float(result.get("keyword_score", 0.0)),
                )
                if best_chunk_id is None:
                    best_chunk_id = key
            if best_chunk_id is not None:
                component_best.append(best_chunk_id)

        ordered_ids = []
        selected = set()
        for chunk_id in component_best:
            if chunk_id not in selected:
                ordered_ids.append(chunk_id)
                selected.add(chunk_id)

        remaining = sorted(
            (
                (key, candidate)
                for key, candidate in candidates.items()
                if key not in selected
            ),
            key=lambda item: item[1]["_query_fusion_score"],
            reverse=True,
        )
        ordered_ids.extend(key for key, _ in remaining)
        selected_results = []
        for chunk_id in ordered_ids[:top_k]:
            candidate = candidates[chunk_id]
            candidate.pop("_query_fusion_score", None)
            selected_results.append(candidate)
        return selected_results

    def _has_sufficient_evidence(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        question: str = "",
    ) -> bool:
        semantic_threshold = getattr(
            self.vector_store,
            "MIN_SEMANTIC_SCORE",
            VectorStoreManager.MIN_SEMANTIC_SCORE,
        )
        keyword_threshold = getattr(
            self.vector_store,
            "MIN_KEYWORD_COVERAGE",
            VectorStoreManager.MIN_KEYWORD_COVERAGE,
        )
        question_lower = (question or "").lower()
        mentions_syllabus = any(
            term in question_lower for term in ("syllabus", "curriculum")
        )
        requests_syllabus = mentions_syllabus and any(
            term in question_lower
            for term in (
                "topic",
                "included",
                "covered",
                "listed",
                "what does",
                "which",
            )
        )
        asks_about_past_questions = any(
            phrase in question_lower
            for phrase in (
                "past question",
                "previous question",
                "question paper",
                "exam question",
            )
        )

        for chunk in retrieved_chunks:
            document_name = str(chunk.get("document_name", "")).lower()
            content = str(chunk.get("content", "")).strip()
            if len(content) < 80:
                continue
            is_syllabus = "syllabus" in document_name
            if is_syllabus and not requests_syllabus:
                continue
            if requests_syllabus and not is_syllabus:
                continue
            if (
                not asks_about_past_questions
                and any(
                    term in document_name
                    for term in ("question_paper", "previous_questions")
                )
            ):
                continue
            if (
                chunk.get("semantic_score", 0.0)
                >= max(semantic_threshold, 0.45)
                or chunk.get("keyword_score", 0.0)
                >= max(keyword_threshold, 0.40)
            ):
                return True

        return False

    @staticmethod
    def _format_sources(
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "document_name": chunk["document_name"],
                "document_id": public_document_id(chunk["source_path"]),
                "page_number": chunk["page_number"],
                "chunk_id": chunk["chunk_id"],
                "hybrid_score": chunk["score"],
                "relevance_score": chunk["score"],
                "snippet": chunk["content"][:300]
                + ("..." if len(chunk["content"]) > 300 else ""),
                "source_path": chunk["source_path"],
            }
            for chunk in retrieved_chunks
        ]

    def get_status(self) -> Dict[str, Any]:
        return self.vector_store.get_status()
