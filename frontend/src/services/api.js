
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export const fetchKBStatus = async () => {
  const response = await apiClient.get('/api/status');
  return response.data;
};

export const fetchDocumentLibrary = async ({
  search,
  subject,
  status,
  page = 1,
  page_size = 20
} = {}) => {
  const response = await apiClient.get('/api/library/documents', {
    params: { search, subject, status, page, page_size }
  });
  return response.data;
};

export const postQuery = async ({ question, top_k = 8 }) => {
  const response = await apiClient.post('/api/query', { question, top_k });
  return response.data;
};

export const postAnalyze = async ({ question, top_k = 6 }) => {
  const response = await apiClient.post('/api/analyze', { question, top_k });
  return response.data;
};

export const triggerReindex = async (force_reindex = false) => {
  const response = await apiClient.post('/api/index', { force_reindex });
  return response.data;
};

/**
 * Constructs the URL to stream the original PDF document at a cited page.
 * @param {string} filename - The PDF document name (e.g. "GATE_2027_CS_Syllabus.pdf")
 * @param {number|string} [pageNumber] - Optional page number to jump to (appends #page=N)
 * @param {string} [sourcePath] - Optional indexed source path to disambiguate duplicate names
 * @returns {string} URL targeting the backend PDF streaming endpoint
 */
export const getDocumentPdfUrl = (filename, pageNumber, sourcePath) => {
  if (!filename) return '#';
  const cleanFilename = String(filename).trim();
  const encodedName = encodeURIComponent(cleanFilename);
  const sourceQuery = sourcePath
    ? `?source_path=${encodeURIComponent(String(sourcePath))}`
    : '';
  const base = `${API_BASE_URL}/api/documents/${encodedName}${sourceQuery}`;
  const parsedPage = parseInt(pageNumber, 10);
  if (!isNaN(parsedPage) && parsedPage > 0) {
    return `${base}#page=${parsedPage}`;
  }
  return base;
};

export const getLibraryPdfUrl = (documentId, pageNumber, download = false) => {
  if (!documentId) return '#';
  const query = download ? '?download=true' : '';
  const parsedPage = parseInt(pageNumber, 10);
  const pageFragment =
    !isNaN(parsedPage) && parsedPage > 0 ? `#page=${parsedPage}` : '';
  return `${API_BASE_URL}/api/library/documents/${encodeURIComponent(documentId)}/pdf${query}${pageFragment}`;
};

export { API_BASE_URL };
