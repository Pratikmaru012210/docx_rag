async function readJsonResponse(response) {
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
  const payload = await readJsonResponse(await fetch('/api/documents'));
  if (!Array.isArray(payload.documents)) {
    throw new Error('The server returned an invalid document list.');
  }
  return payload.documents;
}

export async function getSystemStatus() {
  return readJsonResponse(await fetch('/api/status'));
}

export async function indexAllDocuments() {
  return readJsonResponse(await fetch('/api/index', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  }));
}

export async function reindexDocument(filename) {
  return readJsonResponse(await fetch(
    `/api/documents/${encodeURIComponent(filename)}/reindex`,
    { method: 'POST' }
  ));
}

export async function deleteDocument(filename) {
  return readJsonResponse(await fetch(
    `/api/documents/${encodeURIComponent(filename)}`,
    { method: 'DELETE' }
  ));
}

export async function previewDocument(filename) {
  return readJsonResponse(await fetch(
    `/api/documents/${encodeURIComponent(filename)}/preview`
  ));
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  return readJsonResponse(await fetch('/api/upload', {
    method: 'POST',
    body: formData
  }));
}

export async function exportDocumentTables(filename) {
  return readJsonResponse(await fetch(
    `/api/export-tables?filename=${encodeURIComponent(filename)}`
  ));
}
