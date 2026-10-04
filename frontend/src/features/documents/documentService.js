async function readJsonResponse(response) {
  // Validate the response body first so malformed JSON is distinct from an API error response.
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`The server returned an invalid response (HTTP ${response.status}).`);
  }

  if (!response.ok) {
    throw new Error(payload.detail || `Request failed (HTTP ${response.status}).`);
  }

  return payload;
}

export async function getDocuments() {
  // Fetch and validate the document inventory returned by the backend.
  const payload = await readJsonResponse(await fetch('/api/documents'));
  if (!Array.isArray(payload.documents)) {
    throw new Error('The server returned an invalid document list.');
  }
  return payload.documents;
}

export async function getSystemStatus() {
  // Fetch backend connectivity and configuration status.
  return readJsonResponse(await fetch('/api/status'));
}

export async function indexAllDocuments() {
  // Request indexing of every document currently stored by the backend.
  return readJsonResponse(await fetch('/api/index', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  }));
}

export async function reindexDocument(filename) {
  // Re-index one document without affecting the other stored documents.
  return readJsonResponse(await fetch(
    `/api/documents/${encodeURIComponent(filename)}/reindex`,
    { method: 'POST' }
  ));
}

export async function deleteDocument(filename) {
  // Delete one document and its associated vector records.
  return readJsonResponse(await fetch(
    `/api/documents/${encodeURIComponent(filename)}`,
    { method: 'DELETE' }
  ));
}

export async function previewDocument(filename) {
  // Retrieve parsed chunks for the document inspector.
  return readJsonResponse(await fetch(
    `/api/documents/${encodeURIComponent(filename)}/preview`
  ));
}

export async function uploadDocument(file) {
  // Upload a DOCX as multipart form data for backend storage and sync.
  const formData = new FormData();
  formData.append('file', file);
  return readJsonResponse(await fetch('/api/upload', {
    method: 'POST',
    body: formData
  }));
}

export async function exportDocumentTables(filename) {
  // Request a Markdown export containing the document's parsed tables.
  return readJsonResponse(await fetch(
    `/api/export-tables?filename=${encodeURIComponent(filename)}`
  ));
}
