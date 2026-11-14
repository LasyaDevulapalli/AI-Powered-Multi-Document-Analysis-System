import React from 'react';
import { 
  FileText, 
  Layers, 
  CheckCircle2, 
  Database, 
  HelpCircle, 
  GitMerge, 
  FolderCheck, 
  FileCheck,
  ArrowRight
} from 'lucide-react';

export default function DashboardView({ kbStatus, setActiveTab }) {
  const isIndexed = kbStatus?.is_indexed || false;
  const totalDocs = kbStatus?.total_documents || 0;
  const totalChunks = kbStatus?.total_chunks || 0;

  return (
    <div>
      {/* Dashboard Banner */}
      <div className="dashboard-header-banner">
        <h2>AI-Powered Multi-Document Analysis System</h2>
        <p>Research & Evidence-Grounded Document Intelligence Platform</p>
        <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: '#60a5fa' }}>
          <CheckCircle2 size={18} color="#10b981" />
          <span>Knowledge Base Status: <strong>{isIndexed ? 'Ready' : 'Pending Indexing'}</strong></span>
        </div>
      </div>

      {/* Real Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper">
            <FileText size={24} />
          </div>
          <div>
            <div className="stat-number">{totalDocs}</div>
            <div className="stat-label">Indexed Documents</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper emerald">
            <Layers size={24} />
          </div>
          <div>
            <div className="stat-number">{totalChunks.toLocaleString()}</div>
            <div className="stat-label">Indexed Chunks</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper purple">
            <Database size={24} />
          </div>
          <div>
            <div className="stat-number">{isIndexed ? 'Active' : 'Offline'}</div>
            <div className="stat-label">ChromaDB Store</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper">
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div className="stat-number">Phase 1</div>
            <div className="stat-label">Vector RAG Baseline</div>
          </div>
        </div>
      </div>

      {/* Feature Action Cards */}
      <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.2rem', marginBottom: '1rem', color: '#1e293b' }}>
        System Analysis Features
      </h3>

      <div className="feature-cards-grid">
        <div className="feature-card" onClick={() => setActiveTab('ask')}>
          <div>
            <h3><HelpCircle size={20} color="#2563eb" /> Ask Questions</h3>
            <p>Ask single natural language questions about the prepared knowledge base with grounded answer synthesis.</p>
          </div>
          <button className="feature-card-btn">
            Open Question Interface <ArrowRight size={14} />
          </button>
        </div>

        <div className="feature-card" onClick={() => setActiveTab('multidoc')}>
          <div>
            <h3><GitMerge size={20} color="#7c3aed" /> Multi-Document Analysis</h3>
            <p>Analyze, compare concepts, and synthesize themes across multiple domain documents using vector RAG.</p>
          </div>
          <button className="feature-card-btn">
            Perform Multi-Doc Analysis <ArrowRight size={14} />
          </button>
        </div>

        <div className="feature-card" onClick={() => setActiveTab('kb')}>
          <div>
            <h3><FolderCheck size={20} color="#059669" /> Knowledge Base</h3>
            <p>Explore the prepared domain document collection, chunk metadata, and vector storage details.</p>
          </div>
          <button className="feature-card-btn">
            View Knowledge Base <ArrowRight size={14} />
          </button>
        </div>

        <div className="feature-card" onClick={() => setActiveTab('evidence')}>
          <div>
            <h3><FileCheck size={20} color="#d97706" /> Evidence / Sources</h3>
            <p>Inspect retrieved source passages, exact page numbers, chunk IDs, and retrieval relevance scores.</p>
          </div>
          <button className="feature-card-btn">
            Explore Evidence <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
