# AI-Powered Multi-Document Analysis System using LLMs, RAG & Knowledge Graphs

> **Academic Project:** AI-Powered Multi-Document Analysis System using LLMs, RAG & Knowledge Graphs  
> **Current Phase:** Phase 1 – Domain-Specific Retrieval-Augmented Generation  
> **Initial Domain:** GATE Computer Science and Information Technology (CSE)  
> **Project Status:** Working prototype under evaluation

---

## 1. Project Objective

The objective of this project is to develop an AI-powered multi-document analysis system that enables users to ask questions and obtain context-based answers from a predefined collection of domain-specific documents.

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from a prepared document repository and uses a Large Language Model (LLM) to generate answers based on the retrieved evidence.

Unlike conventional document-question-answering applications that require users to upload PDFs repeatedly, this system operates on a predefined knowledge base that is prepared and indexed in advance.

The initial implementation focuses on GATE CSE preparation, with the architecture designed to support expansion into other academic domains.

## 2. Problem Statement

Large collections of academic documents, examination papers, answer keys and subject materials make it difficult for students to locate and analyze relevant information efficiently.

Conventional LLM-based systems also present challenges:

1. **Hallucination:** Generated responses may contain information that is not supported by the available source material.
2. **Lack of Source Traceability:** Answers may not provide sufficiently precise references to their original documents.
3. **Repeated Document Uploads:** Uploading large document collections for every user session is inefficient.
4. **Multi-Document Analysis:** Identifying and combining relevant information across multiple documents can be challenging.

**Proposed Solution:** Develop a domain-specific document analysis platform using a predefined document repository, hybrid retrieval, persistent vector storage and LLM-based answer generation with source references.

## 3. Phase 1 Scope and Boundaries

### In Scope – Phase 1

- Predefined, administrator-prepared domain document repository.
- PDF discovery, text extraction and document validation.
- Page-aware text chunking with configurable chunk size and overlap.
- Embedding generation using SentenceTransformers or supported external embedding providers.
- Persistent vector storage using ChromaDB.
- Hybrid retrieval combining semantic and keyword-based retrieval with Reciprocal Rank Fusion (RRF).
- Query analysis and decomposition for supported compound questions.
- Context-based LLM answer generation.
- Answer validation and source citation checks.
- Source metadata including document names and page references.
- React-based academic web interface.
- FastAPI backend and REST API endpoints.
- Automated backend tests.

### Out of Scope – Phase 1

The following capabilities are planned for subsequent development:

- Knowledge Graph entity and relationship extraction.
- Graph database integration using technologies such as Neo4j or NetworkX.
- Graph-based retrieval.
- Combined vector and graph retrieval.
- Advanced multi-hop reasoning using Knowledge Graphs.

Knowledge Graph functionality is part of the proposed future development and is not claimed as an implemented Phase 1 feature.

## 4. System Architecture and Workflow

The Phase 1 workflow consists of the following stages:

1. **Prepared Document Repository:** Administrators maintain the predefined domain-specific PDF collection.
2. **Document Processing:** Documents are discovered, validated and processed.
3. **Text Extraction and Chunking:** Extracted text is divided into manageable chunks while preserving page metadata.
4. **Embedding Generation:** Text chunks are converted into vector representations.
5. **Persistent Storage:** Embeddings and associated metadata are stored in ChromaDB.
6. **Hybrid Retrieval:** Relevant passages are retrieved using semantic and keyword-based retrieval with rank fusion.
7. **Query Processing:** Supported compound questions can be decomposed into focused retrieval queries.
8. **LLM Generation:** Retrieved evidence is supplied to the configured LLM for context-based answer generation.
9. **Answer Validation:** Available validation checks examine generated answers and their source references.
10. **Response Presentation:** Answers and supporting source information are presented through the web interface.

### Architecture Overview

```text
       Predefined Domain PDF Repository
                    |
                    v
          Document Processing
                    |
                    v
       Text Extraction and Chunking
                    |
                    v
          Embedding Generation
                    |
                    v
          Persistent ChromaDB
                    |
                    |
             User Question
                    |
                    v
          Query Analysis
                    |
                    v
        Hybrid Retrieval + RRF
                    |
                    v
         Retrieved Evidence
                    |
                    v
          Grounded LLM Engine
                    |
                    v
         Answer Validation
                    |
                    v
       Answer + Source References
                    |
                    v
          React Web Interface
```

## 5. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| ASGI Server | Uvicorn |
| Frontend | React 19 |
| Frontend Build Tool | Vite |
| Styling | CSS |
| Vector Database | ChromaDB |
| Embedding Model | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Additional Embedding Providers | Supported Gemini and OpenAI configurations |
| LLM Providers | Groq and Google Gemini configurations |
| Retrieval | Semantic and keyword-based hybrid retrieval |
| Rank Fusion | Reciprocal Rank Fusion |
| Testing | Pytest and FastAPI TestClient |

Provider availability and model configuration depend on the corresponding environment variables and API credentials.

## 6. Main Application Features

### 6.1 Ask Questions

Allows users to submit natural-language questions against the prepared domain knowledge base.

The system retrieves relevant passages and attempts to generate answers using the available evidence.

### 6.2 Multi-Document Analysis

Provides an interface for questions that require information from multiple documents.

The system retrieves relevant evidence and attempts to synthesize information across the retrieved sources. The quality and completeness of multi-document synthesis remain under evaluation.

### 6.3 Knowledge Base Management

Displays the current knowledge-base status and available indexing information.

The underlying repository is prepared and indexed in advance rather than requiring repeated student uploads.

### 6.4 Source References

Displays available source information associated with retrieved evidence, including document names and page references.

Citation accuracy and direct navigation to the corresponding original PDF pages remain areas for further validation.

### 6.5 Document Library

Provides a document-library interface for accessing prepared PDF resources.

The library loading functionality has an outstanding issue identified during Phase 1 evaluation and requires further testing and correction.

## 7. Project Directory Structure

```text
multi_doc_rag_system/
|
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   |-- routes.py
|   |   |   |-- schemas.py
|   |   |
|   |   |-- core/
|   |   |   |-- config.py
|   |   |   |-- logging_config.py
|   |   |
|   |   |-- document_processing/
|   |   |   |-- __init__.py
|   |   |   |-- base.py
|   |   |   |-- library.py
|   |   |   |-- pdf_extractor.py
|   |   |   |-- processor.py
|   |   |
|   |   |-- image_processing/
|   |   |   |-- __init__.py
|   |   |   |-- image_service.py
|   |   |
|   |   |-- rag/
|   |   |   |-- __init__.py
|   |   |   |-- answer_validation.py
|   |   |   |-- chunker.py
|   |   |   |-- embeddings.py
|   |   |   |-- llm_service.py
|   |   |   |-- pipeline.py
|   |   |   |-- query_analysis.py
|   |   |   |-- vector_store.py
|   |   |
|   |   |-- index.py
|   |   |-- main.py
|   |
|   |-- tests/
|   |-- conftest.py
|   |-- requirements.txt
|
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- assets/
|   |   |-- components/
|   |   |-- services/
|   |   |-- views/
|   |   |-- App.css
|   |   |-- App.jsx
|   |   |-- index.css
|   |   |-- main.jsx
|   |
|   |-- index.html
|   |-- package.json
|   |-- package-lock.json
|   |-- vite.config.js
|
|-- .env.example
|-- .gitignore
|-- README.md
```

**Note:** Prepared PDF datasets, external study-material repositories, local environment files and the persistent ChromaDB database are maintained separately and are not included in this public source-code repository.

## 8. Installation and Setup

### Prerequisites

- Python 3.10 or later.
- Node.js 18 or later.
- npm.
- Git.
- An API key for the selected LLM provider, if using an external LLM.

### Step 1: Clone the Repository

```bash
git clone https://github.com/LasyaDevulapalli/AI-Powered-Multi-Document-Analysis-System.git

cd AI-Powered-Multi-Document-Analysis-System
```

### Step 2: Backend Setup

```bash
cd backend

python -m venv venv
```

Activate the environment.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `backend/.env` file.

Configure the required provider credentials and settings. For example:

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

Use the actual configuration options supported by the backend. Keep all API keys in the backend environment only. Never commit `.env` files.

### Step 4: Prepare the Domain Document Repository

The public GitHub repository does not include the prepared GATE CSE document collection.

The administrator must separately obtain and prepare the permitted domain documents and place them in the expected local directories:

```text
data/
    documents/
    datasets/
        gate_cse_phase1/
            subject_materials/
```

The application is designed to use this prepared repository rather than requiring students to upload documents for every question.

### Step 5: Index the Prepared Documents

From the backend directory, run:

```bash
python -m app.index
```

The indexing process discovers and processes the configured PDF sources and stores the resulting embeddings and metadata in the persistent ChromaDB collection.

Existing indexed data should be backed up before performing any rebuild or collection changes.

### Step 6: Start the Backend

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend health endpoint:

```text
http://127.0.0.1:8000/health
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### Step 7: Start the Frontend

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

Open the application:

```text
http://localhost:5173/
```

## 9. Testing and Evaluation

The backend includes automated tests covering areas such as:

- Document extraction and processing.
- Text chunking.
- Vector-store functionality.
- Query analysis.
- Answer validation.
- Retrieval pipeline behaviour.
- API functionality.
- LLM service behaviour.

**Latest reported automated test result:** 54 backend tests passed.

This result refers to the automated backend test suite, not 54 successful real-world question-answering evaluations.

Live LLM integration testing remains environment-dependent. End-to-end answer correctness, retrieval relevance, citation reliability and multi-document synthesis continue to require evaluation.

## 10. Current Implementation Status and Limitations

Phase 1 has established the core application architecture and a working prototype.

The local development environment previously reported:

- 78 indexed documents.
- 15,873 indexed chunks.
- Persistent ChromaDB storage.
- Working backend and frontend services.

These figures describe the local development knowledge base and are not included in the public GitHub repository. They are not automatically reproduced when another developer clones the source code.

Current areas requiring further improvement include:

1. Retrieval relevance for certain technical and numerical questions.
2. Completeness and accuracy of generated answers.
3. Consistency of source citation validation.
4. Evidence coverage in multi-document synthesis.
5. Document Library loading functionality.
6. Direct navigation from source references to the corresponding PDF pages.

The system may return a no-direct-match response when sufficient supporting evidence is not found or validated. This behaviour and the underlying retrieval quality remain under evaluation.

## 11. Phase 2: Future Enhancements

Phase 2 is intended to extend the existing vector-based RAG architecture with Knowledge Graph capabilities.

Planned enhancements include:

- Entity and relationship extraction from indexed documents.
- Knowledge Graph construction.
- Graph database integration.
- Graph-based retrieval.
- Combined vector and graph retrieval.
- Multi-hop reasoning across related documents.
- Comparative evaluation of vector-only RAG and Graph-RAG approaches.

These enhancements are planned developments and are not part of the current Phase 1 implementation.

---

## 12. Project Repository

**GitHub:**  
https://github.com/LasyaDevulapalli/AI-Powered-Multi-Document-Analysis-System

---

*This project is being developed as an academic implementation, with Phase 1 focused on building and evaluating a domain-specific multi-document RAG system for GATE CSE preparation.*