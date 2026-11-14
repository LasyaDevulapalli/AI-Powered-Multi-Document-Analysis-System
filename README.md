# AI-Powered Multi-Document Analysis System using LLMs, RAG & Knowledge Graphs (Phase 1)

> **Academic Project Title:** AI-Powered Multi-Document Analysis System using LLMs, RAG & Knowledge Graphs  
> **Current Focus:** Phase 1 Implementation — Domain LLM & Vector RAG Infrastructure  
> **Target Audience / Guide:** Academic Faculty Review Board  

---

## 1. Project Objective

The primary objective of Phase 1 is to build a domain-specific multi-document Question-Answering (QA) system powered by Retrieval-Augmented Generation (RAG). 

Unlike typical conversational AI interfaces where users are forced to upload PDF files repeatedly during every session, this system operates over a **pre-indexed, domain-specific document repository** prepared in advance by administrators. Users interact directly with the knowledge base, submitting natural language questions and receiving answers that are strictly grounded in retrieved source documents, complete with precise page-level citations.

---

## 2. Problem Statement

Standard Large Language Models (LLMs) suffer from three critical academic limitations when applied to specialized domains:
1. **Hallucination:** LLMs often generate plausible but factually incorrect assertions when lacking exact knowledge.
2. **Knowledge Cutoff & Lack of Provenance:** Standard models cannot cite exact page numbers or document sources for their statements.
3. **Repetitive Upload Overhead:** Uploading massive PDF collections per user session is inefficient, bandwidth-heavy, and unscalable.

**Phase 1 Solution:** Pre-index domain documents into a persistent vector store (ChromaDB), combine semantic and BM25-style lexical retrieval with rank fusion, enforce strict evidence-only generation, and display actual document and page-level source references.

---

## 3. Phase 1 Scope & Boundary

### In Scope (Phase 1):
* Pre-indexed domain document storage (`data/documents/`)
* Automated text extraction & validation from PDF files
* Page-aware text chunking with configurable `chunk_size` and `chunk_overlap`
* Modular embedding generation (SentenceTransformers `all-MiniLM-L6-v2` / Google Gemini `text-embedding-004`)
* Persistent vector database storage using ChromaDB
* Hybrid semantic and BM25-style lexical retrieval with reciprocal-rank fusion, deduplication, and source metadata preservation
* Grounded prompt generation requiring document-name and page citations for factual claims
* Source citation mapping (Document Name, Page Number, Chunk ID, Relevance Score)
* Professional academic web dashboard (React + Vite)
* Standalone indexing CLI (`python -m app.index`) & REST API (`FastAPI`)
* Automated backend test suite: 54 tests passed in the latest reported run. Live LLM integration testing remains environment-dependent.

### Out of Scope for Phase 1 (Prepared for Phase 2):
* Knowledge Graph (KG) entity-relation extraction *(Phase 2)*
* Graph database (Neo4j / NetworkX) integration *(Phase 2)*
* Hybrid vector + graph retrieval *(Phase 2)*
* Fine-tuning LLM weights from scratch *(Not required)*

---

## 4. System Architecture & Workflow

```
┌────────────────────────────────────────────────────────┐
│             Predefined Domain Documents                │
│                 (data/documents/*.pdf)                 │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            Document Processing & Extraction            │
│       (Readability validation & page text extraction)  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                  Text Chunking Unit                    │
│   (Configurable Chunk Size: 600, Overlap: 100 chars)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                 Embedding Generation                   │
│        (Modular: SentenceTransformers / Gemini)        │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│           Persistent ChromaDB Vector Store             │
│            (vector_store/ - Survives Restarts)         │
└──────────────────────────┬─────────────────────────────┘
                           │
       User Question ─────┤ (Natural Language Query)
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│          Hybrid Top-K Retrieval + Rank Fusion           │
│     (Semantic, BM25-style lexical, source metadata)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               Grounded LLM Prompt Engine               │
│          (Strictly restricted to retrieved context)    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            Grounded Answer + Page Citations            │
│         (Document Name, Page Number, Relevance %)      │
└────────────────────────────────────────────────────────┘
```

---

## 5. Technology Stack

* **Backend Framework:** Python 3.14, FastAPI, Uvicorn
* **PDF Text Extraction:** `pypdf` (with empty/unreadable document detection)
* **Text Chunking:** Recursive overlap chunker preserving page metadata
* **Vector Database:** ChromaDB (persistent local store)
* **Embedding Models:** SentenceTransformers (`all-MiniLM-L6-v2` - default local/zero-cost) or Google Gemini (`text-embedding-004`)
* **LLM Engine:** Groq API (`llama-3.3-70b-versatile` / OpenAI-compatible endpoint) or Google Gemini API (`gemini-3.8-flash`) with fallback synthesis for offline evaluation
* **Frontend UI:** React 19, Vite, Vanilla CSS Academic Design System
* **Testing:** Pytest, FastAPI TestClient

---

## 6. Directory Structure

```
multi_doc_rag_system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py            # FastAPI endpoints (/health, /api/query, /api/index, /api/status)
│   │   │   └── schemas.py           # Pydantic validation schemas
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings (Chunk size, paths, models)
│   │   │   └── logging_config.py    # Structured logging setup
│   │   ├── document_processing/
│   │   │   ├── base.py              # Base document extractor & data models
│   │   │   ├── pdf_extractor.py     # PDF text extraction & validation
│   │   │   └── processor.py         # Directory discovery & extraction manager
│   │   ├── rag/
│   │   │   ├── chunker.py           # Text chunker with page metadata preservation
│   │   │   ├── embeddings.py        # Modular embedding service (SentenceTransformers / Gemini)
│   │   │   ├── vector_store.py      # ChromaDB persistence & similarity search
│   │   │   ├── llm_service.py       # Grounded LLM service (Groq / Gemini / Mock)
│   │   │   └── pipeline.py          # RAG pipeline orchestrator
│   │   ├── main.py                  # FastAPI application entrypoint
│   │   └── index.py                 # Standalone CLI indexing script
│   ├── tests/
│   │   ├── test_extractor.py        # Extractor unit tests
│   │   ├── test_chunker.py          # Chunker unit tests
│   │   ├── test_vector_store.py     # Vector store unit tests
│   │   └── test_api.py              # API integration tests
│   ├── conftest.py                  # Pytest configuration
│   └── requirements.txt             # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx           # Academic header with status badge
│   │   │   ├── KBStatusPanel.jsx    # Pre-indexed document list display
│   │   │   ├── QueryPanel.jsx       # Natural language input & sample questions
│   │   │   ├── AnswerDisplay.jsx    # Grounded answer & performance metrics
│   │   │   ├── SourcesList.jsx      # Source citation cards with page & score
│   │   │   └── ErrorAlert.jsx       # User-facing error component
│   │   ├── services/
│   │   │   └── api.js               # Axios API client
│   │   ├── App.jsx                  # Main dashboard layout
│   │   ├── index.css                # Academic Vanilla CSS design system
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── data/
│   └── documents/                   # Predefined domain PDF documents
├── vector_store/                    # Persistent ChromaDB collection directory
├── .env.example                     # Environment template
└── README.md                        # Academic documentation
```

---

## 7. Installation & Setup Instructions

### Prerequisites
* Python 3.10+ (Tested on Python 3.14)
* Node.js 18+ and npm

### Step 1: Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create `backend/.env` for backend-only configuration. Keep provider API keys out of frontend files and client-side environment variables. Add the following settings to `backend/.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
GROQ_MODEL_NAME=llama-3.3-70b-versatile
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
CHUNK_SIZE=600
CHUNK_OVERLAP=100
TOP_K=4
CHROMA_COLLECTION_NAME=domain_knowledge_base
```

### Step 3: Index Domain Documents (CLI)
Before launching the server, process and index the prepared domain documents.
The indexer reads PDFs from `data/documents/` and recursively from
`data/datasets/gate_cse_phase1/subject_materials/`. Subject-material PDFs are
added only when extracted text has at least 500 characters and an alphabetic
character ratio of at least 0.35; rejected files are reported rather than
indexed as evidence.
```bash
python -m app.index
```
Existing chunk IDs are preserved and skipped during indexing. The command
reports discovered, extracted, skipped, and indexed counts, along with subject
folders represented in the extracted corpus. `--force` intentionally refuses
to clear or replace the active ChromaDB collection. For a rebuild, back up
`vector_store/`, set `CHROMA_COLLECTION_NAME` to a new collection name in
`backend/.env`, and index into that separate collection.

### Step 4: Run Backend Server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Verify backend health by opening `http://127.0.0.1:8000/health`.

### Step 5: Frontend Setup & Run
Open a new terminal window:
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
Access the academic web application at `http://127.0.0.1:5173/`.

---

## 8. Automated Testing

Run the comprehensive pytest suite covering text extraction, chunking, ChromaDB vector search, API health, query validation, and no-result handling:
```bash
cd backend
venv\Scripts\pytest.exe -v
```
Report the results from the test run performed in the current environment; no coverage or accuracy level is assumed here.

---

## 9. Example Research Questions

Try asking the following pre-loaded domain questions in the UI:
1. *"What is Retrieval-Augmented Generation (RAG) and why is it used?"*
2. *"What chunk size and overlap parameters yield optimal retrieval precision?"*
3. *"Why does pure vector search fail for complex cross-document entity relations?"*
4. *"How are LLM hallucinations prevented in this domain system?"*

---

## 10. Phase 2 Compatibility & Future Work

Phase 1 provides a clean, modular foundation for Phase 2 extensions:
* **Knowledge Graph Construction:** Entity-relation extraction will automatically parse chunks into nodes and edges.
* **Graph Retrieval:** Add graph traversal alongside the Phase 1 dense/lexical hybrid retriever.
* **Cross-Document Reasoning:** Resolve multi-hop dependencies across document boundaries.
* **Comparative Benchmark:** Evaluate accuracy, hallucination rate, and context recall between Vector-only RAG (Phase 1) vs. Graph-RAG (Phase 2).
