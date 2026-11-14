import React from 'react';
import { 
  Database, 
  FolderCheck, 
  FileText, 
  Layers, 
  RefreshCw, 
  ShieldAlert, 
  CheckCircle2, 
  Cpu, 
  HardDrive,
  ExternalLink 
} from 'lucide-react';
import { getDocumentPdfUrl, getLibraryPdfUrl } from '../services/api';

export default function KnowledgeBaseView({ kbStatus, onReindex, isIndexing }) {
  const isIndexed = kbStatus?.is_indexed || false;
  const totalDocs = kbStatus?.total_documents || 0;
  const totalChunks = kbStatus?.total_chunks || 0;
  const docDetails = kbStatus?.documents_details || [];
  const docNames = kbStatus?.document_names || [];

  return (
    <div>
      <div className="card-panel" style={{ marginBottom: '1.5rem' }}>
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <FolderCheck size={20} color="#059669" />
              Prepared Knowledge Base Repository
            </div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.2rem' }}>
              Pre-indexed domain document collection stored in ChromaDB vector database.
            </div>
          </div>
          <span className="grounded-badge" style={{ backgroundColor: '#ecfdf5', color: '#059669' }}>
            Status: {isIndexed ? 'Indexed ✓' : 'Pending'}
          </span>
        </div>

        {/* Real Backend Statistics Bar */}
        <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="stat-card" style={{ padding: '0.9rem 1.1rem' }}>
            <div className="stat-icon-wrapper emerald" style={{ width: '40px', height: '40px' }}>
              <FileText size={20} />
            </div>
            <div>
              <div className="stat-number" style={{ fontSize: '1.25rem' }}>{totalDocs}</div>
              <div className="stat-label">Prepared Documents</div>
            </div>
          </div>

          <div className="stat-card" style={{ padding: '0.9rem 1.1rem' }}>
            <div className="stat-icon-wrapper" style={{ width: '40px', height: '40px' }}>
              <Layers size={20} />
            </div>
            <div>
              <div className="stat-number" style={{ fontSize: '1.25rem' }}>{totalChunks.toLocaleString()}</div>
              <div className="stat-label">Vector Chunks</div>
            </div>
          </div>

          <div className="stat-card" style={{ padding: '0.9rem 1.1rem' }}>
            <div className="stat-icon-wrapper purple" style={{ width: '40px', height: '40px' }}>
              <HardDrive size={20} />
            </div>
            <div>
              <div className="stat-number" style={{ fontSize: '1.25rem' }}>ChromaDB</div>
              <div className="stat-label">Persistent Collection</div>
            </div>
          </div>
        </div>

        {/* Document Metadata Table */}
        <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.05rem', color: '#1e293b', marginBottom: '0.5rem' }}>
          Indexed Document Collection
        </h3>

        <div className="table-responsive">
          {docDetails.length > 0 ? (
            <table className="kb-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Format</th>
                  <th>Total Pages</th>
                  <th>Chunks Extracted</th>
                  <th>Indexing Status</th>
                </tr>
              </thead>
              <tbody>
                {docDetails.map((doc, idx) => (
                  <tr key={idx}>
                    <td>
                      <a
                        href={doc.document_id
                          ? getLibraryPdfUrl(doc.document_id, 1)
                          : getDocumentPdfUrl(doc.document_name, 1)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-doc-link"
                        title={`Open ${doc.document_name} in a new tab`}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}
                      >
                        <FileText size={16} />
                        <span>{doc.document_name}</span>
                        <ExternalLink size={12} style={{ opacity: 0.6 }} />
                      </a>
                    </td>
                    <td>PDF Document</td>
                    <td>{doc.pages} Page(s)</td>
                    <td>{doc.chunks} Chunk(s)</td>
                    <td>
                      <span style={{ 
                        fontSize: '0.78rem', 
                        fontWeight: 600, 
                        color: '#059669', 
                        background: '#ecfdf5', 
                        padding: '0.2rem 0.5rem', 
                        borderRadius: '4px' 
                      }}>
                        {doc.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : docNames.length > 0 ? (
            <table className="kb-table">
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {docNames.map((name, idx) => (
                  <tr key={idx}>
                    <td>
                      <a
                        href={getDocumentPdfUrl(name, 1)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-doc-link"
                        title={`Open ${name} in a new tab`}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}
                      >
                        <FileText size={16} />
                        <span>{name}</span>
                        <ExternalLink size={12} style={{ opacity: 0.6 }} />
                      </a>
                    </td>
                    <td>Indexed ✓</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontStyle: 'italic' }}>
              No documents currently indexed in knowledge base.
            </div>
          )}
        </div>
      </div>

      {/* Separate Developer / Admin Controls Box */}
      <div className="admin-section-box">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#b45309', marginBottom: '0.4rem' }}>
          <ShieldAlert size={18} />
          Developer / Admin Workflow Only
        </div>
        <p style={{ fontSize: '0.84rem', color: '#78350f', marginBottom: '1rem', lineHeight: '1.45' }}>
          This workflow scans <code>data/documents/</code> and the prepared GATE subject-material folders, extracts readable text, generates vector embeddings, and adds new chunks to the persistent ChromaDB collection. Normal student queries do not require re-indexing.
        </p>

        <button
          type="button"
          className="btn-secondary"
          onClick={onReindex}
          disabled={isIndexing}
        >
          <RefreshCw size={15} className={isIndexing ? 'spinner' : ''} />
          {isIndexing ? 'Re-indexing Documents Directory...' : 'Developer/Admin: Re-index Knowledge Base'}
        </button>
      </div>
    </div>
  );
}
