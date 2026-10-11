import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import {
  deleteDocument,
  getDocuments,
  uploadDocument
} from './documentService.js';

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

test('loads documents from the existing API route', async () => {
  let requestedUrl;
  const documents = [{ filename: 'sop.docx', chunks_count: 3 }];
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return Response.json({ documents });
  };

  assert.deepEqual(await getDocuments(), documents);
  assert.equal(requestedUrl, '/api/documents');
});

test('rejects malformed document-list responses', async () => {
  globalThis.fetch = async () => Response.json({ documents: null });

  await assert.rejects(getDocuments(), /invalid document list/);
});

test('uploads the DOCX to the backend indexing endpoint', async () => {
  let requestedUrl;
  let requestOptions;
  const response = {
    filename: 'sop.docx',
    indexed: true,
    index_details: { status: 'success', chunks_indexed: 3 }
  };
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestOptions = options;
    return Response.json(response);
  };
  const file = new File(['docx content'], 'sop.docx');

  assert.deepEqual(await uploadDocument(file), response);
  assert.equal(requestedUrl, '/api/upload');
  assert.equal(requestOptions.method, 'POST');
  assert.ok(requestOptions.body instanceof FormData);
  assert.equal(requestOptions.body.get('file').name, 'sop.docx');
});

test('deletes the backend document and its associated vectors', async () => {
  let requestedUrl;
  let requestOptions;
  const response = { status: 'success', filename: 'sop.docx' };
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestOptions = options;
    return Response.json(response);
  };

  assert.deepEqual(await deleteDocument('sop.docx'), response);
  assert.equal(requestedUrl, '/api/documents/sop.docx');
  assert.equal(requestOptions.method, 'DELETE');
});
