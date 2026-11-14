
import React, { useState } from 'react';
import {
  Send,
  HelpCircle,
  Sliders,
  ShieldCheck,
  Clock,
  FileCheck,
  AlertTriangle,
  BookMarked,
  Hash,
  Info,
  ExternalLink
} from 'lucide-react';
import { getLibraryPdfUrl } from '../services/api';
import AnswerMarkdown from '../components/AnswerMarkdown';

const SINGLE_QUESTIONS = [
  'What is Retrieval-Augmented Generation (RAG) and why is it used?',
  'What chunk size and overlap parameters yield optimal retrieval precision?',
  'Why does pure vector search fail for complex cross-document entity relations?',
  'How are LLM hallucinations prevented in this domain system?'
];

export default function AskQuestionsView({
  onQuerySubmit,
  isLoading,
  queryResponse,
  totalChunks = 8
}) {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(4);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (question.trim() && !isLoading) {
      onQuerySubmit({
        question: question.trim(),
        top_k: topK
      });
    }
  };

  const isTopKExceeded = topK > totalChunks;

  return (
    <div>
      <div className="card-panel" style={{ marginBottom: '1.5rem' }}>
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <HelpCircle size={20} color="#2563eb" />
              Ask a Question about the Prepared Knowledge Base
            </div>

            <div
              style={{
                fontSize: '0.82rem',
                color: '#64748b',
                marginTop: '0.2rem'
              }}
            >
              Document repository prepared in advance — No student document
              upload required.
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <textarea
            className="query-textarea"
            placeholder="Enter your question grounded in the prepared knowledge base..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isLoading}
          />

          <details className="advanced-settings-drawer">
            <summary>
              <Sliders
                size={14}
                style={{ display: 'inline', marginRight: '4px' }}
              />
              Advanced Retrieval Settings (Top-K Context Depth)
            </summary>

            <div className="slider-group">
              <div className="slider-header">
                <span>Retrieved Context Chunks (Top-K):</span>
                <strong>{topK} Chunks</strong>
              </div>

              <input
                type="range"
                min="1"
                max="10"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                disabled={isLoading}
              />

              {isTopKExceeded && (
                <div
                  style={{
                    fontSize: '0.75rem',
                    color: '#d97706',
                    marginTop: '0.4rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem'
                  }}
                >
                  <Info size={12} />
                  <span>
                    Notice: Top-K ({topK}) exceeds total indexed chunks (
                    {totalChunks}). The system may return fewer unique chunks
                    than requested.
                  </span>
                </div>
              )}
            </div>
          </details>

          <div
            style={{
              display: 'flex',
              gap: '1rem',
              alignItems: 'center'
            }}
          >
            <button
              type="submit"
              className="btn-primary"
              disabled={!question.trim() || isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner">⏳</span>
                  Analyzing Question...
                </>
              ) : (
                <>
                  <Send size={16} />
                  Analyze Question
                </>
              )}
            </button>
          </div>
        </form>

        <div
          style={{
            marginTop: '1.25rem',
            paddingTop: '1rem',
            borderTop: '1px solid #e2e8f0'
          }}
        >
          <div
            style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: '#64748b',
              marginBottom: '0.5rem'
            }}
          >
            Sample Domain Research Questions:
          </div>

          <div className="sample-questions-grid">
            {SINGLE_QUESTIONS.map((q, idx) => (
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

      {isLoading && (
        <div className="loading-box">
          <span
            className="spinner"
            style={{ fontSize: '1.8rem', display: 'inline-block' }}
          >
            ⚙️
          </span>

          <h4
            style={{
              fontSize: '1.05rem',
              color: '#1e293b',
              marginTop: '0.5rem'
            }}
          >
            Analyzing Question &amp; Retrieving Evidence...
          </h4>

          <div className="loading-steps">
            <span className="step-item">
              <span className="spinner">🔄</span> Searching vector database
            </span>
            <span className="step-item">
              Extracting top context chunks
            </span>
            <span className="step-item">
              Synthesizing grounded answer
            </span>
          </div>
        </div>
      )}

      {queryResponse && !isLoading && (
        <div>
          <div className="answer-card">
            <div className="answer-header-bar">
              <div
                className={`grounded-badge ${queryResponse.is_grounded ? '' : 'un-grounded'
                  }`}
              >
                {queryResponse.is_grounded ? (
                  <ShieldCheck size={14} />
                ) : (
                  <AlertTriangle size={14} />
                )}

                {queryResponse.is_grounded
                  ? 'Grounded in Prepared Knowledge Base'
                  : 'No Direct Match'}
              </div>

              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                <Clock
                  size={12}
                  style={{ display: 'inline', marginRight: '3px' }}
                />
                <span>{queryResponse.elapsed_time}s</span>

                <span style={{ margin: '0 8px' }}>•</span>

                <FileCheck
                  size={12}
                  style={{ display: 'inline', marginRight: '3px' }}
                />
                <span>{queryResponse.retrieved_count} Chunks Retrieved</span>
              </div>
            </div>

            <h3
              style={{
                fontFamily: 'Outfit, sans-serif',
                fontSize: '1.1rem',
                marginBottom: '0.75rem',
                color: '#1e293b'
              }}
            >
              AI Grounded Answer
            </h3>

            <div className="answer-body answer-markdown">
              <AnswerMarkdown
                answer={queryResponse.answer}
                sources={queryResponse.sources || []}
              />
            </div>
          </div>

          {queryResponse.sources &&
            queryResponse.sources.length > 0 && (
              <div className="card-panel">
                <div
                  className="panel-title"
                  style={{ marginBottom: '1rem' }}
                >
                  <BookMarked size={18} color="#2563eb" />
                  Evidence Used ({queryResponse.sources.length} Context Blocks)
                </div>

                <div className="sources-grid">
                  {queryResponse.sources.map((src, idx) => {
                    const scorePct = Math.round(
                      (src.hybrid_score ?? src.relevance_score ?? 0) * 100
                    );

                    return (
                      <div
                        key={src.chunk_id || `${src.document_name}-${src.page_number}-${idx}`}
                        className="source-card"
                      >
                        <div className="source-card-header">
                          <a
                            href={getLibraryPdfUrl(src.document_id, src.page_number)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="source-doc-link"
                            title={`Open ${src.document_name} at Page ${src.page_number || 1} in a new tab`}
                          >
                            <ExternalLink size={12} style={{ flexShrink: 0 }} />
                            <span className="source-doc-name">
                              {src.document_name}
                            </span>
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

                        <div
                          className="relevance-bar-container"
                          title={`Normalized hybrid ranking score: ${scorePct}/100; not a confidence or match probability`}
                        >
                          <div
                            className="relevance-bar-fill"
                            style={{
                              width: `${Math.max(
                                0,
                                Math.min(100, scorePct)
                              )}%`
                            }}
                          />
                        </div>

                        <div
                          style={{
                            fontSize: '0.72rem',
                            color: '#64748b',
                            marginBottom: '0.4rem'
                          }}
                        >
                          Hybrid ranking score:{' '}
                          <strong>{scorePct}/100</strong>
                        </div>

                        <div className="source-snippet">
                          "{src.snippet}"
                        </div>

                        <div
                          style={{
                            fontSize: '0.68rem',
                            color: '#94a3b8',
                            marginTop: '0.4rem',
                            fontFamily: 'monospace'
                          }}
                        >
                          <Hash
                            size={10}
                            style={{
                              display: 'inline',
                              marginRight: '2px'
                            }}
                          />
                          Chunk ID: {src.chunk_id || 'N/A'}
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
