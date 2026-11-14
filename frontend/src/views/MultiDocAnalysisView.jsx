import React, { useState } from 'react';
import { 
  GitMerge, 
  Send, 
  BookOpen, 
  Layers, 
  CheckCircle2, 
  FileCheck, 
  Clock,
  Sparkles,
  Hash,
  ExternalLink,
  AlertTriangle
} from 'lucide-react';
import { getLibraryPdfUrl } from '../services/api';
import AnswerMarkdown from '../components/AnswerMarkdown';

const MULTI_DOC_QUESTIONS = [
  "Compare the information about RAG architecture and chunking parameters across the documents.",
  "What common concepts appear across the document collection?",
  "Summarize the differences between pure vector search limitations and Knowledge Graph benefits.",
  "What major themes are discussed across these research papers?"
];

export default function MultiDocAnalysisView({ onAnalyzeSubmit, isLoading, analysisResponse }) {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onAnalyzeSubmit({ question: question.trim(), top_k: 6 });
    }
  };

  return (
    <div>
      <div className="card-panel" style={{ marginBottom: '1.5rem' }}>
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <GitMerge size={20} color="#7c3aed" />
              Multi-Document Analysis & Cross-Document Synthesis
            </div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.2rem' }}>
              Phase 1: Vector-based RAG analysis across multiple domain documents.
            </div>
          </div>
          <span className="phase-badge" style={{ background: '#f3e8ff', color: '#7c3aed', border: '1px solid #ddd6fe' }}>
            Phase 1: Vector RAG Analysis
          </span>
        </div>

        <form onSubmit={handleSubmit}>
          <textarea
            className="query-textarea"
            placeholder="Enter a question requiring comparison, synthesis, or theme extraction across multiple documents..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isLoading}
          />

          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button
              type="submit"
              className="btn-primary"
              style={{ backgroundColor: '#7c3aed' }}
              disabled={!question.trim() || isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner">⏳</span>
                  Synthesizing Across Documents...
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  Run Multi-Document Analysis
                </>
              )}
            </button>
          </div>
        </form>

        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', marginBottom: '0.5rem' }}>
            Sample Cross-Document Analysis Prompts:
          </div>
          <div className="sample-questions-grid">
            {MULTI_DOC_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                type="button"
                className="sample-chip"
                onClick={() => setQuestion(q)}
                disabled={isLoading}
              >
                "{q}"
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stepped Loading Box */}
      {isLoading && (
        <div className="loading-box">
          <span className="spinner" style={{ fontSize: '1.8rem', display: 'inline-block' }}>🧬</span>
          <h4 style={{ fontSize: '1.05rem', color: '#1e293b', marginTop: '0.5rem' }}>Performing Multi-Document Vector Retrieval & Cross-Synthesis...</h4>
          <div className="loading-steps">
            <span className="step-item"><span className="spinner">🔄</span> Searching vector database</span>
            <span className="step-item">Retrieving chunks from multiple documents</span>
            <span className="step-item">Generating cross-document synthesis</span>
          </div>
        </div>
      )}

      {/* Synthesis Result Display */}
      {analysisResponse && !isLoading && (
        <div>
          {/* Documents Considered Bar */}
          {analysisResponse.documents_considered && analysisResponse.documents_considered.length > 0 && (
            <div className="documents-considered-bar">
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>
                <BookOpen size={14} style={{ display: 'inline', marginRight: '4px' }} />
                Documents Considered ({analysisResponse.documents_considered.length} Source Files):
              </div>
              <div className="doc-badge-list">
                {analysisResponse.documents_considered.map((docName, idx) => (
                  <a
                    key={idx}
                    href={getLibraryPdfUrl(
                      analysisResponse.sources.find(
                        (source) => source.document_name === docName
                      )?.document_id,
                      1
                    )}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="doc-badge doc-badge-link"
                    title={`Open ${docName} in a new tab`}
                    style={{ textDecoration: 'none' }}
                  >
                    <CheckCircle2 size={12} color="#10b981" />
                    <span>{docName}</span>
                    <ExternalLink size={10} style={{ marginLeft: '2px', opacity: 0.7 }} />
                  </a>
                ))}
              </div>
            </div>
          )}

          <div className="answer-card">
            <div className="answer-header-bar">
              <span className={`grounded-badge ${analysisResponse.is_grounded ? '' : 'un-grounded'}`}>
                {analysisResponse.is_grounded
                  ? <FileCheck size={14} />
                  : <AlertTriangle size={14} />}
                {analysisResponse.is_grounded
                  ? 'Grounded Multi-Document Synthesis'
                  : 'Unverified / Evidence Notice'}
              </span>

              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                <Clock size={12} style={{ display: 'inline', marginRight: '3px' }} />
                <span>{analysisResponse.elapsed_time}s</span>
                <span style={{ margin: '0 8px' }}>•</span>
                <Layers size={12} style={{ display: 'inline', marginRight: '3px' }} />
                <span>{analysisResponse.retrieved_count} Context Chunks</span>
              </div>
            </div>

            <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.15rem', marginBottom: '0.75rem', color: '#1e293b' }}>
              Cross-Document Synthesis Analysis
            </h3>

            <AnswerMarkdown
              className="answer-body answer-markdown"
              answer={analysisResponse.answer}
              sources={analysisResponse.sources || []}
            />
          </div>

          {/* Supporting Evidence Passages */}
          {analysisResponse.sources && analysisResponse.sources.length > 0 && (
            <div className="card-panel">
              <div className="panel-title" style={{ marginBottom: '1rem' }}>
                <Layers size={18} color="#7c3aed" />
                Evidence Passages Considered
              </div>

              <div className="sources-grid">
                {analysisResponse.sources.map((src, idx) => {
                  const scorePct = Math.round(
                    (src.hybrid_score ?? src.relevance_score ?? 0) * 100
                  );
                  return (
                    <div key={idx} className="source-card">
                      <div className="source-card-header">
                        <a
                          href={getLibraryPdfUrl(src.document_id, src.page_number)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-doc-link"
                          title={`Open ${src.document_name} at Page ${src.page_number || 1} in a new tab`}
                        >
                          <ExternalLink size={12} style={{ flexShrink: 0 }} />
                          <span className="source-doc-name">{src.document_name}</span>
                        </a>
                        <a
                          href={getLibraryPdfUrl(src.document_id, src.page_number)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-page-tag source-page-link"
                          title={`Jump to Page ${src.page_number || 1}`}
                        >
                          Page {src.page_number || 'N/A'}
                        </a>
                      </div>

                      <div className="relevance-bar-container" title={`Normalized hybrid ranking score: ${scorePct}/100; not a confidence or match probability`}>
                        <div className="relevance-bar-fill" style={{ width: `${Math.max(0, scorePct)}%`, backgroundColor: '#7c3aed' }} />
                      </div>

                      <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: '0.4rem' }}>
                        Hybrid ranking score: <strong>{scorePct}/100</strong>
                      </div>

                      <div className="source-snippet">
                        "{src.snippet}"
                      </div>

                      <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '0.4rem', fontFamily: 'monospace' }}>
                        <Hash size={10} style={{ display: 'inline', marginRight: '2px' }} />
                        Chunk ID: {src.chunk_id}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
