import React from 'react';
import { BookMarked, Hash, Layers } from 'lucide-react';

export default function SourcesList({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <div className="sources-panel-header">
        <BookMarked size={18} color="#2563eb" />
        Supporting Source References ({sources.length})
      </div>

      <div className="sources-grid">
        {sources.map((src, idx) => {
          const scorePct = Math.round(
            (src.hybrid_score ?? src.relevance_score ?? 0) * 100
          );

          return (
            <div key={idx} className="source-card">
              <div className="source-card-header">
                <span className="source-doc-name">{src.document_name}</span>
                <span className="source-page-tag">
                  Page {src.page_number || 'N/A'}
                </span>
              </div>

              <div               className="relevance-bar-container" title={`Normalized hybrid ranking score: ${scorePct}/100; not a confidence or match probability`}>
                <div 
                  className="relevance-bar-fill" 
                  style={{ width: `${Math.max(0, scorePct)}%` }} 
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b', marginBottom: '0.4rem' }}>
                <span>Hybrid ranking score: <strong>{scorePct}/100</strong></span>
              </div>

              <div className="source-snippet">
                "{src.snippet}"
              </div>

              <div className="source-chunk-id">
                <Hash size={10} style={{ display: 'inline', marginRight: '2px' }} />
                Chunk ID: {src.chunk_id}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
