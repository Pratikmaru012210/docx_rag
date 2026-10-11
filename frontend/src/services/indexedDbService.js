// IndexedDB wrapper for storing and managing uploaded SOP documents in Chrome/browser
const DB_NAME = 'sop_rag_db';
const DB_VERSION = 1;
const STORE_DOCUMENTS = 'documents';

/**
 * Open or upgrade the IndexedDB instance.
 * @returns {Promise<IDBDatabase>}
 */
export function openIndexedDB() {
  return new Promise((resolve, reject) => {
    if (!('indexedDB' in window)) {
      reject(new Error('IndexedDB is not supported by your browser.'));
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_DOCUMENTS)) {
        const store = db.createObjectStore(STORE_DOCUMENTS, { keyPath: 'id' });
        store.createIndex('filename', 'filename', { unique: false });
        store.createIndex('uploadedAt', 'uploadedAt', { unique: false });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Failed to open IndexedDB'));
  });
}

/**
 * Save an uploaded DOCX file and its metadata to IndexedDB.
 * @param {File} file
 * @returns {Promise<Object>} The saved document record
 */
export async function saveDocumentToIndexedDB(file) {
  const db = await openIndexedDB();
  const fileBuffer = await file.arrayBuffer();

  const record = {
    id: `${Date.now()}_${file.name}`,
    filename: file.name,
    size_bytes: file.size,
    size_kb: Number((file.size / 1024).toFixed(1)),
    mime_type: file.type || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    uploadedAt: new Date().toISOString(),
    chunks_count: 0,
    tables_count: 0,
    storage: 'IndexedDB',
    // Storing blob/buffer for offline retrieval or download
    fileData: fileBuffer
  };

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_DOCUMENTS], 'readwrite');
    const store = transaction.objectStore(STORE_DOCUMENTS);
    const request = store.put(record);

    request.onsuccess = () => resolve(record);
    request.onerror = () => reject(request.error || new Error('Failed to save document to IndexedDB'));
  });
}

/**
 * Retrieve all stored documents from IndexedDB.
 * @returns {Promise<Array<Object>>}
 */
export async function getAllDocumentsFromIndexedDB() {
  const db = await openIndexedDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_DOCUMENTS], 'readonly');
    const store = transaction.objectStore(STORE_DOCUMENTS);
    const request = store.getAll();

    request.onsuccess = () => {
      // Return metadata omitting bulky array buffers for listing
      const docs = (request.result || []).map((doc) => ({
        id: doc.id,
        filename: doc.filename,
        size_kb: doc.size_kb,
        size_bytes: doc.size_bytes,
        uploadedAt: doc.uploadedAt,
        chunks_count: doc.chunks_count || 0,
        tables_count: doc.tables_count || 0,
        storage: 'IndexedDB'
      }));
      resolve(docs);
    };
    request.onerror = () => reject(request.error || new Error('Failed to load documents from IndexedDB'));
  });
}

/**
 * Retrieve a single document including its fileData by filename or id.
 * @param {string} idOrFilename
 * @returns {Promise<Object|null>}
 */
export async function getDocumentFromIndexedDB(idOrFilename) {
  const db = await openIndexedDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_DOCUMENTS], 'readonly');
    const store = transaction.objectStore(STORE_DOCUMENTS);

    const getReq = store.get(idOrFilename);
    getReq.onsuccess = () => {
      if (getReq.result) {
        resolve(getReq.result);
        return;
      }

      // If not matched by ID, try searching by filename
      const index = store.index('filename');
      const indexReq = index.get(idOrFilename);
      indexReq.onsuccess = () => resolve(indexReq.result || null);
      indexReq.onerror = () => reject(indexReq.error);
    };
    getReq.onerror = () => reject(getReq.error);
  });
}

/**
 * Delete a document from IndexedDB by filename or id.
 * @param {string} idOrFilename
 * @returns {Promise<boolean>}
 */
export async function deleteDocumentFromIndexedDB(idOrFilename) {
  const db = await openIndexedDB();
  const doc = await getDocumentFromIndexedDB(idOrFilename);

  if (!doc) {
    return false;
  }

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_DOCUMENTS], 'readwrite');
    const store = transaction.objectStore(STORE_DOCUMENTS);
    const request = store.delete(doc.id);

    request.onsuccess = () => resolve(true);
    request.onerror = () => reject(request.error || new Error('Failed to delete document from IndexedDB'));
  });
}
