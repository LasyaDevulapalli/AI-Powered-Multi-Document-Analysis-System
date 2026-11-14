
import os
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb

from app.document_processing.base import DocumentChunk
from app.document_processing.library import public_document_id
from app.core.config import settings
from app.core.logging_config import logger


class VectorStoreManager:
    """Persistent ChromaDB store with semantic, lexical, and topic-aware retrieval."""

    RRF_CONSTANT = 60
    SEMANTIC_WEIGHT = 1.0
    LEXICAL_WEIGHT = 1.0
    MIN_SEMANTIC_SCORE = 0.25
    MIN_KEYWORD_COVERAGE = 0.15

    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "being", "to", "of", "in", "on", "at", "for", "from", "by",
        "with", "and", "or", "but", "as", "it", "its", "this", "that",
        "these", "those", "what", "which", "who", "how", "why", "when",
        "where", "do", "does", "did", "can", "could", "would", "should",
        "please", "explain", "tell", "me", "about", "according", "prepared",
        "document", "documents", "include", "included", "section", "topics",
        "topic", "following", "using", "computer", "science",
    }

    OS_TERMS = {
        "system call", "system calls", "process", "processes", "thread",
        "threads", "inter-process communication", "concurrency",
        "synchronization", "deadlock", "cpu scheduling", "io scheduling",
        "memory management", "virtual memory", "file systems",
    }

    GRAPH_DEFINITION_PHRASES = (
        "a graph is",
        "graph is a",
        "graph consists of",
        "graph is defined as",
        "set of vertices and edges",
        "set of nodes and edges",
        "vertices connected by edges",
        "nodes connected by edges",
    )

    def __init__(self, collection_name: Optional[str] = None):
        self.persist_directory = str(settings.VECTOR_STORE_DIR)
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        logger.info(
            "Initializing Persistent ChromaDB client at: "
            f"{self.persist_directory}"
        )

        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _normalize_token(token: str) -> str:
        """Apply lightweight normalization without external NLP dependencies."""
        token = token.lower()

        if len(token) > 5 and token.endswith("ies"):
            return token[:-3] + "y"

        if len(token) > 5 and token.endswith("ing"):
            token = token[:-3]
        elif len(token) > 4 and token.endswith("ed"):
            token = token[:-2]
        elif len(token) > 4 and token.endswith("es"):
            token = token[:-2]
        elif len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]

        return token

    @classmethod
    def _tokens(cls, text: str) -> set:
        """Extract normalized words and identifiers."""
        raw_tokens = re.findall(
            r"[a-zA-Z]+|[0-9]+(?:\.[0-9]+)?",
            (text or "").lower(),
        )

        return {
            cls._normalize_token(token)
            for token in raw_tokens
            if token not in cls.STOPWORDS
            and (
                len(token) > 1
                or token.isdigit()
                or token in {"n", "k", "v", "e", "o"}
            )
        }

    @classmethod
    def _bm25_scores(cls, query_tokens: set, documents: List[str]) -> List[float]:
        """Return dependency-free BM25 scores for a query over candidate chunks."""
        if not query_tokens or not documents:
            return [0.0] * len(documents)

        tokenized_documents = [
            re.findall(
                r"[a-zA-Z]+|[0-9]+(?:\.[0-9]+)?",
                (document or "").lower(),
            )
            for document in documents
        ]
        tokenized_documents = [
            [
                cls._normalize_token(token)
                for token in tokens
                if token not in cls.STOPWORDS
                and (len(token) > 1 or token.isdigit() or token in {"n", "k", "v", "e", "o"})
            ]
            for tokens in tokenized_documents
        ]

        document_count = len(tokenized_documents)
        average_length = (
            sum(len(tokens) for tokens in tokenized_documents) / document_count
            if document_count
            else 0.0
        )
        document_frequencies = {
            term: sum(term in set(tokens) for tokens in tokenized_documents)
            for term in query_tokens
        }

        scores = []
        for tokens in tokenized_documents:
            frequencies: Dict[str, int] = {}
            for token in tokens:
                frequencies[token] = frequencies.get(token, 0) + 1

            score = 0.0
            for term in query_tokens:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                doc_frequency = document_frequencies[term]
                inverse_frequency = (
                    1.0
                    + (document_count - doc_frequency + 0.5)
                    / (doc_frequency + 0.5)
                )
                inverse_frequency = math.log(inverse_frequency)
                length_normalization = (
                    1.5 * (1.0 - 0.75 + 0.75 * len(tokens) / average_length)
                    if average_length
                    else 1.5
                )
                score += (
                    inverse_frequency
                    * frequency
                    * (1.5 + 1.0)
                    / (frequency + length_normalization)
                )
            scores.append(score)

        return scores

    @classmethod
    def _keyword_score(
        cls,
        query_tokens: set,
        content: str,
        document_name: str,
    ) -> float:
        """Measure query-term coverage in the passage and filename."""
        if not query_tokens:
            return 0.0

        content_tokens = cls._tokens(content)
        filename_tokens = cls._tokens(document_name)

        content_coverage = (
            len(query_tokens & content_tokens) / len(query_tokens)
        )
        filename_coverage = (
            len(query_tokens & filename_tokens) / len(query_tokens)
        )

        return min(
            1.0,
            content_coverage + 0.35 * filename_coverage,
        )

    @staticmethod
    def _document_type_boost(
        question: str,
        document_name: str,
    ) -> float:
        """Prefer document types explicitly requested by the question."""
        q = (question or "").lower()
        name = (document_name or "").lower()
        boost = 0.0

        asks_syllabus = any(
            term in q
            for term in ("syllabus", "syllabi", "curriculum", "topics included")
        )
        is_syllabus = "syllabus" in name

        asks_answer_key = any(
            term in q
            for term in (
                "answer key", "correct answer", "official answer",
                "answer for question", "answer to question",
            )
        )
        is_answer_key = "answer_key" in name or "answer key" in name

        asks_question_paper = any(
            term in q
            for term in ("question paper", "exam paper", "paper question")
        )
        is_question_paper = (
            "question_paper" in name or "question paper" in name
        )

        if asks_syllabus and is_syllabus:
            boost += 0.20
        elif asks_syllabus:
            boost -= 0.05

        if asks_answer_key and is_answer_key:
            boost += 0.25
        elif asks_answer_key and is_question_paper:
            boost -= 0.08

        if asks_question_paper and is_question_paper:
            boost += 0.12

        return boost

    @classmethod
    def _topic_relevance_adjustment(
        cls,
        question: str,
        content: str,
        document_name: str,
    ) -> float:
        """Apply lightweight topic-specific ranking heuristics."""
        q = (question or "").lower()
        text = (content or "").lower()
        name = (document_name or "").lower()
        adjustment = 0.0

        asks_os = (
            "operating system" in q
            or re.search(r"\bos\b", q) is not None
        )

        if asks_os:
            matched_os_terms = sum(
                1 for term in cls.OS_TERMS if term in text
            )

            if matched_os_terms >= 3:
                adjustment += 0.30
            elif matched_os_terms >= 1:
                adjustment += 0.12
            elif "syllabus" in name:
                adjustment -= 0.20

        asks_graph_definition = (
            "what is a graph" in q
            or "define a graph" in q
            or "definition of a graph" in q
        )

        if asks_graph_definition:
            matched_phrases = sum(
                1
                for phrase in cls.GRAPH_DEFINITION_PHRASES
                if phrase in text
            )

            if matched_phrases:
                adjustment += 0.25
            elif "control flow graph" in text or "control-flow graph" in text:
                adjustment -= 0.08

        return adjustment

    @classmethod
    def _is_graph_definition_question(cls, question: str) -> bool:
        """Identify questions asking for a general graph definition."""
        q = (question or "").lower()

        return any(
            phrase in q
            for phrase in (
                "what is a graph",
                "define a graph",
                "definition of a graph",
            )
        )

    @classmethod
    def _has_direct_graph_definition_evidence(
        cls,
        content: str,
        document_name: str,
    ) -> bool:
        """
        Require explanatory wording for general graph-definition questions.
        Exam-question passages are not accepted as general definitions.
        """
        text = (content or "").lower()
        name = (document_name or "").lower()

        if "question_paper" in name or "question paper" in name:
            return False

        return any(
            phrase in text
            for phrase in cls.GRAPH_DEFINITION_PHRASES
        )

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        if not chunks:
            return 0
        if len(chunks) != len(embeddings):
            raise ValueError(
                "The number of chunk records must match the number of embeddings."
            )

        existing_ids = set(
            self.collection.get(
                ids=[chunk.chunk_id for chunk in chunks],
                include=["metadatas"],
            ).get("ids", [])
        )
        seen_incoming = set()
        new_items = []
        for chunk, embedding in zip(chunks, embeddings):
            if (
                chunk.chunk_id in existing_ids
                or chunk.chunk_id in seen_incoming
            ):
                continue
            new_items.append((chunk, embedding))
            seen_incoming.add(chunk.chunk_id)

        if not new_items:
            logger.info(
                "No new chunks to add; existing ChromaDB records were preserved."
            )
            return 0

        new_chunks = [item[0] for item in new_items]
        new_embeddings = [item[1] for item in new_items]
        metadatas = []
        for chunk in new_chunks:
            metadata = {
                key: value
                for key, value in chunk.metadata.items()
                if value is not None
            }
            metadata["document_id"] = metadata.get(
                "document_id"
            ) or chunk.document_id
            metadata["document_name"] = metadata.get(
                "document_name"
            ) or chunk.document_name
            if chunk.page_number is not None:
                metadata.setdefault("page_number", chunk.page_number)
            metadata["chunk_id"] = chunk.chunk_id
            metadata["source_path"] = metadata.get(
                "source_path"
            ) or chunk.source_path
            metadatas.append(metadata)

        self.collection.add(
            ids=[chunk.chunk_id for chunk in new_chunks],
            embeddings=new_embeddings,
            documents=[chunk.content for chunk in new_chunks],
            metadatas=metadatas,
        )

        logger.info(
            f"Successfully added {len(new_chunks)} new chunks to ChromaDB "
            f"collection '{self.collection_name}'"
        )

        return len(new_chunks)

    def query(
        self,
        query_embedding: List[float],
        top_k: int = None,
        question: str = "",
        diversify_documents: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fuse semantic and BM25 rankings, preserving source metadata."""
        k = top_k or settings.TOP_K
        total_items = self.collection.count()

        if total_items == 0:
            logger.warning("Query attempted on an empty ChromaDB store.")
            return []

        actual_k = min(max(1, k), total_items)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=total_items,
            include=["documents", "metadatas", "distances"],
        )

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        query_tokens = self._tokens(question)
        bm25_scores = self._bm25_scores(query_tokens, docs)
        candidates = []

        for i, content in enumerate(docs):
            content = content or ""
            metadata = metas[i] or {}
            source_path = metadata.get("source_path") or ""
            document_name = metadata.get("document_name") or (
                os.path.basename(source_path) if source_path else "Unknown"
            )
            page_number = metadata.get("page_number", 1)
            chunk_id = metadata.get("chunk_id") or (
                ids[i] if i < len(ids) else ""
            )

            distance = float(distances[i]) if i < len(distances) else 1.0
            semantic_score = max(0.0, min(1.0, 1.0 - distance))

            keyword_score = self._keyword_score(
                query_tokens,
                content,
                document_name,
            )

            candidates.append(
                {
                    "content": content,
                    "metadata": metadata,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score,
                    "bm25_score": bm25_scores[i],
                    "document_name": document_name,
                    "page_number": page_number,
                    "chunk_id": chunk_id,
                    "source_path": source_path,
                    "semantic_rank": 0,
                    "lexical_rank": 0,
                }
            )

        semantic_order = sorted(
            range(len(candidates)),
            key=lambda index: candidates[index]["semantic_score"],
            reverse=True,
        )
        lexical_order = sorted(
            range(len(candidates)),
            key=lambda index: (
                candidates[index]["bm25_score"],
                candidates[index]["keyword_score"],
            ),
            reverse=True,
        )
        semantic_ranks = {
            candidate_index: rank
            for rank, candidate_index in enumerate(semantic_order, 1)
        }
        lexical_ranks = {
            candidate_index: rank
            for rank, candidate_index in enumerate(lexical_order, 1)
        }
        max_rrf_score = (
            self.SEMANTIC_WEIGHT + self.LEXICAL_WEIGHT
        ) / (self.RRF_CONSTANT + 1)

        ranked = []
        seen_chunks = set()
        for index, candidate in enumerate(candidates):
            candidate["semantic_rank"] = semantic_ranks[index]
            candidate["lexical_rank"] = lexical_ranks[index]

            chunk_key = candidate["chunk_id"] or (
                candidate["document_name"],
                candidate["page_number"],
                candidate["content"],
            )
            if chunk_key in seen_chunks:
                continue
            seen_chunks.add(chunk_key)

            if not (
                candidate["semantic_score"] >= self.MIN_SEMANTIC_SCORE
                or candidate["keyword_score"] >= self.MIN_KEYWORD_COVERAGE
            ):
                continue

            rrf_score = (
                self.SEMANTIC_WEIGHT
                / (self.RRF_CONSTANT + candidate["semantic_rank"])
                + self.LEXICAL_WEIGHT
                / (self.RRF_CONSTANT + candidate["lexical_rank"])
            ) / max_rrf_score
            score = (
                rrf_score
                + self._document_type_boost(
                    question,
                    candidate["document_name"],
                )
                + self._topic_relevance_adjustment(
                    question,
                    candidate["content"],
                    candidate["document_name"],
                )
            )
            candidate["score"] = round(max(0.0, min(1.0, score)), 4)
            candidate["semantic_score"] = round(
                candidate["semantic_score"], 4
            )
            candidate["keyword_score"] = round(
                candidate["keyword_score"], 4
            )
            candidate["bm25_score"] = round(candidate["bm25_score"], 4)
            ranked.append(candidate)

        ranked.sort(key=lambda item: item["score"], reverse=True)

        # Filter general graph-definition questions to passages that
        # explicitly explain the concept, not just graph exam problems.
        if self._is_graph_definition_question(question):
            ranked = [
                item
                for item in ranked
                if self._has_direct_graph_definition_evidence(
                    item["content"],
                    item["document_name"],
                )
            ]

        if diversify_documents:
            retrieved = []
            seen_documents = set()
            for item in ranked:
                if item["document_name"] in seen_documents:
                    continue
                retrieved.append(item)
                seen_documents.add(item["document_name"])
                if len(retrieved) == actual_k:
                    break

            selected_chunks = {
                item["chunk_id"] for item in retrieved
            }
            for item in ranked:
                if len(retrieved) == actual_k:
                    break
                if item["chunk_id"] not in selected_chunks:
                    retrieved.append(item)
                    selected_chunks.add(item["chunk_id"])
        else:
            retrieved = ranked[:actual_k]

        logger.info(
            f"Hybrid retrieval returned {len(retrieved)} chunks "
            f"from {total_items} candidates (top_k={actual_k})."
        )

        return retrieved

    def get_status(self) -> Dict[str, Any]:
        count = self.collection.count()
        doc_map = {}

        if count > 0:
            sample = self.collection.get(include=["metadatas"])

            for metadata in sample.get("metadatas") or []:
                if not metadata or "document_name" not in metadata:
                    continue

                name = metadata["document_name"]
                page_number = metadata.get("page_number", 1)
                source_path = metadata.get("source_path")
                key = str(Path(source_path).resolve()).casefold() if source_path else name

                if key not in doc_map:
                    doc_map[key] = {
                        "document_name": name,
                        "source_path": source_path,
                        "subject": metadata.get("subject"),
                        "chunks": 0,
                        "max_page": 1,
                    }

                doc_map[key]["chunks"] += 1

                if (
                    isinstance(page_number, int)
                    and page_number > doc_map[key]["max_page"]
                ):
                    doc_map[key]["max_page"] = page_number

        doc_details = [
            {
                "document_name": info["document_name"],
                "document_id": (
                    public_document_id(info["source_path"])
                    if info["source_path"]
                    else None
                ),
                "subject": info["subject"],
                "pages": info["max_page"],
                "chunks": info["chunks"],
                "status": "Indexed ✓",
                "error": None,
            }
            for info in doc_map.values()
        ]

        return {
            "is_indexed": count > 0,
            "total_chunks": count,
            "total_documents": len(doc_map),
            "document_names": [
                info["document_name"] for info in doc_map.values()
            ],
            "documents_details": doc_details,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
        }

    def get_document_records(self) -> List[Dict[str, Any]]:
        """Return per-file indexing counts and metadata for the library API."""
        collection_data = self.collection.get(include=["metadatas"])
        records: Dict[str, Dict[str, Any]] = {}
        for metadata in collection_data.get("metadatas") or []:
            if not metadata:
                continue
            source_path = metadata.get("source_path")
            document_name = metadata.get("document_name")
            if not source_path or not document_name:
                continue
            key = str(Path(source_path).resolve()).casefold()
            record = records.setdefault(
                key,
                {
                    "source_path": source_path,
                    "document_name": document_name,
                    "subject": metadata.get("subject"),
                    "page_count": 0,
                    "chunk_count": 0,
                },
            )
            record["chunk_count"] += 1
            page_number = metadata.get("page_number")
            if isinstance(page_number, int):
                record["page_count"] = max(record["page_count"], page_number)
        return list(records.values())

    def clear_collection(self):
        """Clear the collection only when explicitly requested."""
        logger.info(f"Clearing collection '{self.collection_name}'...")

        self.client.delete_collection(name=self.collection_name)

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
