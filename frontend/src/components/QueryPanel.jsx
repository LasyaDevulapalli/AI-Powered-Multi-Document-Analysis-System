import React, { useState } from 'react';
import { Send, HelpCircle, Sliders, Sparkles } from 'lucide-react';

const SAMPLE_QUESTIONS = [
  "What is Retrieval-Augmented Generation (RAG) and why is it used?",
  "What chunk size and overlap parameters yield optimal retrieval precision?",
  "Why does pure vector search fail for complex cross-document entity relations?",
  "How are LLM hallucinations prevented in this domain system?"
];

export default function QueryPanel({ onQuerySubmit, isLoading }) {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(4);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onQuerySubmit({ question: question.trim(), top_k: topK });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit(e);
    }
  };

  return (
    <div className="card-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Sparkles size={18} color="#2563eb" />
          Natural Language Domain Query
        </div>
        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Press Ctrl + Enter to submit</span>
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          className="query-textarea"
          placeholder="Ask a question grounded in the prepared domain documents..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />

        <div className="slider-group">
          <div className="slider-header">
            <span>
              <Sliders size={12} style={{ display: 'inline', marginRight: '4px' }} />
              Retrieved Context Depth (Top-K Chunks):
            </span>
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
        </div>

        <button
          type="submit"
          className="btn-primary"
          disabled={!question.trim() || isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner">⏳</span>
              Retrieving Context & Synthesizing Answer...
            </>
          ) : (
            <>
              <Send size={16} />
              Submit Query to RAG Pipeline
            </>
          )}
        </button>
      </form>

      <div className="sample-questions-section">
        <div className="sample-heading">
          <HelpCircle size={12} style={{ display: 'inline', marginRight: '4px' }} />
          Sample Domain Research Questions
        </div>
        {SAMPLE_QUESTIONS.map((q, idx) => (
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
  );
}
