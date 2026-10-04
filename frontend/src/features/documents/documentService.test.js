import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { getDocuments } from './documentService.js';

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
