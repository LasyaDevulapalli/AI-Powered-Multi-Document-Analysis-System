import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Download,
  ExternalLink,
  FileText,
  Search
} from 'lucide-react';
import { fetchDocumentLibrary, getLibraryPdfUrl } from '../services/api';

const STATUS_LABELS = {
  indexed: 'Indexed and searchable',
  available_not_indexed: 'Available, not indexed',
  skipped_quality: 'Skipped by text-quality check',
  failed_extraction: 'Extraction failed',
  missing_source: 'Indexed record, source missing'
};

export default function DocumentLibraryView() {
  const [library, setLibrary] = useState(null);
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError('');
      try {
        const result = await fetchDocumentLibrary({
          search: search.trim() || undefined,
          subject: subject || undefined,
          status: status || undefined,
          page,
          page_size: 20
        });
        if (active) setLibrary(result);
      } catch (requestError) {
        if (active) {
          setError(
            requestError.response?.data?.detail ||
              'Could not load the prepared document library.'
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }, search ? 250 : 0);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [search, subject, status, page]);

  const resetFilters = () => {
    setSearch('');
    setSubject('');
    setStatus('');
    setPage(1);
  };

  return (
    <section className="document-library">
      <div className="card-panel">
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <BookOpen size={20} color="#2563eb" />
              Prepared GATE CSE Document Library
            </div>
            <p className="library-intro">
              Browse and open administrator-prepared study materials. Students
              do not need to upload documents to ask questions.
            </p>
          </div>
        </div>

        <div className="library-stats" aria-live="polite">
          <div>
            <strong>{library?.indexed_documents ?? '—'}</strong>
            <span>Indexed PDFs</span>
          </div>
          <div>
            <strong>{library?.total_chunks?.toLocaleString() ?? '—'}</strong>
            <span>Indexed chunks</span>
          </div>
          <div>
            <strong>{library?.total_documents ?? '—'}</strong>
            <span>PDF files found</span>
          </div>
          {library?.status_counts &&
            Object.entries(library.status_counts)
              .filter(([name]) => name !== 'indexed')
              .map(([name, count]) => (
                <div key={name}>
                  <strong>{count}</strong>
                  <span>{STATUS_LABELS[name] || name}</span>
                </div>
              ))}
        </div>

        <div className="library-filters">
          <label className="library-search">
            <span className="sr-only">Search document names or topics</span>
            <Search size={16} aria-hidden="true" />
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="Search document names or topics"
            />
          </label>
          <label>
            <span className="sr-only">Filter by subject</span>
            <select
              value={subject}
              onChange={(event) => {
                setSubject(event.target.value);
                setPage(1);
              }}
            >
              <option value="">All subjects</option>
              {(library?.subjects || []).map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>
          <label>
            <span className="sr-only">Filter by indexing status</span>
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setPage(1);
              }}
            >
              <option value="">All statuses</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <button type="button" className="btn-secondary" onClick={resetFilters}>
            Clear filters
          </button>
        </div>

        {error && <div className="library-error" role="alert">{error}</div>}
        {loading && <p className="library-message">Loading prepared PDFs…</p>}
        {!loading && !error && library?.documents.length === 0 && (
          <p className="library-message">No documents match these filters.</p>
        )}

        {!loading && !error && library?.documents.length > 0 && (
          <>
            <div className="table-responsive">
              <table className="kb-table library-table">
                <thead>
                  <tr>
                    <th>Study material</th>
                    <th>Subject</th>
                    <th>Pages</th>
                    <th>Chunks</th>
                    <th>Indexing status</th>
                    <th>Access</th>
                  </tr>
                </thead>
                <tbody>
                  {library.documents.map((document) => (
                    <tr key={document.document_id}>
                      <td>
                        <strong>{document.document_name}</strong>
                        <small>{document.original_filename}</small>
                      </td>
                      <td>{document.subject}</td>
                      <td>{document.page_count || '—'}</td>
                      <td>{document.chunk_count.toLocaleString()}</td>
                      <td>
                        <span className={`library-status ${document.indexed_status}`}>
                          {STATUS_LABELS[document.indexed_status] || document.indexed_status}
                        </span>
                      </td>
                      <td>
                        {document.available_pdf ? (
                          <div className="library-actions">
                            <a
                              href={getLibraryPdfUrl(document.document_id, 1)}
                              target="_blank"
                              rel="noopener noreferrer"
                              aria-label={`Open ${document.original_filename}`}
                            >
                              <ExternalLink size={16} /> Open
                            </a>
                            <a
                              href={getLibraryPdfUrl(document.document_id, undefined, true)}
                              aria-label={`Download ${document.original_filename}`}
                            >
                              <Download size={16} /> Download
                            </a>
                          </div>
                        ) : (
                          <span className="library-unavailable">
                            <FileText size={14} /> Source unavailable
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="library-pagination">
              <span>
                {library.filtered_total} matching PDFs · Page {library.page} of{' '}
                {Math.max(library.total_pages, 1)}
              </span>
              <div>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={page >= library.total_pages}
                  onClick={() => setPage((value) => value + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
