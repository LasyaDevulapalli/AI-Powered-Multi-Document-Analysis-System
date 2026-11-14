import React from 'react';
import { 
  BookOpen, 
  LayoutDashboard, 
  HelpCircle, 
  GitMerge, 
  Database, 
  FileCheck,
  LibraryBig
} from 'lucide-react';

export default function Header({ activeTab, setActiveTab, kbStatus }) {
  const isIndexed = kbStatus?.is_indexed || false;
  const totalChunks = kbStatus?.total_chunks || 0;
  const totalDocs = kbStatus?.total_documents || 0;

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'ask', label: 'Ask Questions', icon: HelpCircle },
    { id: 'multidoc', label: 'Multi-Document Analysis', icon: GitMerge, badge: 'Phase 1 Vector' },
    { id: 'kb', label: 'Knowledge Base', icon: Database },
    { id: 'library', label: 'Document Library', icon: LibraryBig },
    { id: 'evidence', label: 'Evidence / Sources', icon: FileCheck },
  ];

  return (
    <header className="app-header">
      <div className="header-top-row">
        <div className="header-title-section">
          <h1>
            <BookOpen size={24} color="#60a5fa" />
            AI-Powered Multi-Document Analysis System
            <span className="phase-badge">Phase 1: Vector RAG</span>
          </h1>
          <p className="header-subtitle">
            Domain-specific document intelligence using Retrieval-Augmented Generation
          </p>
        </div>

        <div className="header-status-pill">
          <span className={`status-dot ${isIndexed ? 'online' : 'warning'}`}></span>
          <span>Knowledge Base: <strong>{isIndexed ? 'Ready ●' : 'Indexing Required'}</strong> ({totalDocs} Docs, {totalChunks} Chunks)</span>
        </div>
      </div>

      {/* Top 5-Section Navigation Bar */}
      <div className="nav-tabs-container">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-tab-btn ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={16} />
              <span>{item.label}</span>
              {item.badge && (
                <span style={{ 
                  fontSize: '0.65rem', 
                  background: 'rgba(59, 130, 246, 0.2)', 
                  color: '#93c5fd', 
                  padding: '1px 5px', 
                  borderRadius: '4px',
                  fontWeight: 600
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </header>
  );
}
