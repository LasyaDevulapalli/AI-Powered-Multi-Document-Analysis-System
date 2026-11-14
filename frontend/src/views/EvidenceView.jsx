import React, { useState } from 'react';
import { FileCheck, BookMarked, Search, Hash, Info, Layers, ExternalLink } from 'lucide-react';
import { getLibraryPdfUrl } from '../services/api';

export default function EvidenceView({ queryResponse, analysisResponse }) {
  const [searchTerm, setSearchTerm] = useState('');

  // Combine sources from recent query or analysis
  const rawSources = [
    ...(queryResponse?.sources || []),
    ...(analysisResponse?.sources || [])
  ];

  // Remove exact duplicates by chunk_id
  const uniqueSourcesMap = new Map();
  rawSources.forEach(src => {
    if (src.chunk_id && !uniqueSourcesMap.has(src.chunk_id)) {
      uniqueSourcesMap.set(src.chunk_id, src);
    }
  });

  const sources = Array.from(uniqueSourcesMap.values());

  const filteredSources = sources.filter(src => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      src.document_name.toLowerCase().includes(term) ||
      src.snippet.toLowerCase().includes(term) ||
      src.chunk_id.toLowerCase().includes(term)
    );
  });

  return (
    <div>
      <div className="card-panel" style={{ marginBottom: '1.5rem' }}>
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <FileCheck size={20} color="#d97706" />
              Evidence & Provenance Explorer
            </div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.2rem' }}>
              Inspect retrieved context passages, page numbers, and chunk IDs from vector retrieval.
            </div>
          </div>
        </div>

        {/* Search / Filter Input */}
        <div style={{ position: 'relative', marginBottom: '1rem' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#94a3b8' }} />
          <input
            type="text"
            className="query-textarea"
            style={{ minHeight: 'auto', paddingLeft: '2.3rem', height: '40px' }}
            placeholder="Filter evidence by document name or keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {filteredSources.length > 0 ? (
          <div className="sources-grid">
            {filteredSources.map((src, idx) => {
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
                    <div className="relevance-bar-fill" style={{ width: `${Math.max(0, scorePct)}%`, backgroundColor: '#d97706' }} />
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
        ) : (
          <div className="empty-state">
            <BookMarked size={48} />
            <h3>No Evidence Loaded Yet</h3>
            <p>
              Submit a question in <strong>Ask Questions</strong> or run a query in <strong>Multi-Document Analysis</strong> to inspect retrieved evidence passages here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
