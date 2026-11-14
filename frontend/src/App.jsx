import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import DashboardView from './views/DashboardView';
import AskQuestionsView from './views/AskQuestionsView';
import MultiDocAnalysisView from './views/MultiDocAnalysisView';
import KnowledgeBaseView from './views/KnowledgeBaseView';
import EvidenceView from './views/EvidenceView';
import DocumentLibraryView from './views/DocumentLibraryView';
import ErrorAlert from './components/ErrorAlert';
import { fetchKBStatus, postQuery, postAnalyze, triggerReindex } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [kbStatus, setKbStatus] = useState(null);
  
  const [queryResponse, setQueryResponse] = useState(null);
  const [analysisResponse, setAnalysisResponse] = useState(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadKBStatus = async () => {
    try {
      const statusData = await fetchKBStatus();
      setKbStatus(statusData);
    } catch (err) {
      console.error('Failed to fetch KB status:', err);
      setErrorMessage('Backend service unavailable. Ensure FastAPI server is running on port 8000.');
    }
  };

  useEffect(() => {
    loadKBStatus();
  }, []);

  const handleQuerySubmit = async ({ question, top_k }) => {
    setIsLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const res = await postQuery({ question, top_k });
      setQueryResponse(res);
    } catch (err) {
      console.error('Query error:', err);
      const detail = err.response?.data?.detail || 'Failed to communicate with RAG Backend API.';
      setErrorMessage(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeSubmit = async ({ question, top_k }) => {
    setIsLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const res = await postAnalyze({ question, top_k });
      setAnalysisResponse(res);
    } catch (err) {
      console.error('Analysis error:', err);
      const detail = err.response?.data?.detail || 'Failed to process multi-document analysis.';
      setErrorMessage(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReindex = async () => {
    setIsIndexing(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const res = await triggerReindex(true);
      await loadKBStatus();
      setSuccessMessage(res.message || 'Knowledge Base successfully re-indexed into ChromaDB vector store.');
    } catch (err) {
      console.error('Reindexing error:', err);
      setErrorMessage('Failed to re-index Knowledge Base repository.');
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <>
      <Header 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        kbStatus={kbStatus}
      />

      <main className="app-container">
        {errorMessage && <ErrorAlert message={errorMessage} />}
        {successMessage && (
          <div style={{
            backgroundColor: '#ecfdf5',
            border: '1px solid #a7f3d0',
            color: '#047857',
            padding: '0.85rem 1rem',
            borderRadius: '6px',
            fontSize: '0.88rem',
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span>✓ {successMessage}</span>
            <button 
              onClick={() => setSuccessMessage('')}
              style={{ background: 'none', border: 'none', color: '#047857', cursor: 'pointer', fontWeight: 700 }}
            >
              ✕
            </button>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <DashboardView 
            kbStatus={kbStatus} 
            setActiveTab={setActiveTab} 
          />
        )}

        {activeTab === 'ask' && (
          <AskQuestionsView 
            onQuerySubmit={handleQuerySubmit}
            isLoading={isLoading}
            queryResponse={queryResponse}
            totalChunks={kbStatus?.total_chunks || 0}
          />
        )}

        {activeTab === 'multidoc' && (
          <MultiDocAnalysisView 
            onAnalyzeSubmit={handleAnalyzeSubmit}
            isLoading={isLoading}
            analysisResponse={analysisResponse}
          />
        )}

        {activeTab === 'kb' && (
          <KnowledgeBaseView 
            kbStatus={kbStatus}
            onReindex={handleReindex}
            isIndexing={isIndexing}
          />
        )}

        {activeTab === 'library' && <DocumentLibraryView />}

        {activeTab === 'evidence' && (
          <EvidenceView 
            queryResponse={queryResponse}
            analysisResponse={analysisResponse}
          />
        )}
      </main>
    </>
  );
}
