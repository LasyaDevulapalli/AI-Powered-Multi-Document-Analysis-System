import React from 'react';
import { FileText, FolderCheck, Cpu, Layers } from 'lucide-react';

export default function KBStatusPanel({ kbStatus }) {
  const docNames = kbStatus?.document_names || [];

  return (
    <div className="card-panel" style={{ marginTop: '1.25rem' }}>
      <div className="panel-header">
        <div className="panel-title">
          <FolderCheck size={18} color="#2563eb" />
          Predefined Knowledge Base
        </div>
        <span className="predefined-source-tag">data/documents/</span>
      </div>

      <div style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '0.85rem' }}>
        The system queries against this pre-indexed domain collection. No document upload is needed per question.
      </div>

      {docNames.length > 0 ? (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {docNames.map((name, idx) => (
            <li 
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.82rem',
                padding: '0.4rem 0.6rem',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                marginBottom: '0.35rem',
                fontWeight: 500,
                color: '#334155'
              }}
            >
              <FileText size={14} color="#2563eb" />
              <span style={{ wordBreak: 'break-all' }}>{name}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontStyle: 'italic' }}>
          No document metadata loaded. Run indexing to scan documents directory.
        </div>
      )}

      <div style={{
        marginTop: '1rem',
        paddingTop: '0.75rem',
        borderTop: '1px dashed #e2e8f0',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '0.75rem',
        color: '#64748b'
      }}>
        <span><Layers size={12} style={{ display: 'inline', marginRight: '3px' }} /> ChromaDB Persistence: Active</span>
        <span><Cpu size={12} style={{ display: 'inline', marginRight: '3px' }} /> Embeddings: MiniLM-L6-v2</span>
      </div>
    </div>
  );
}
