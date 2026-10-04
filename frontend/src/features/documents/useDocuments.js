import { useCallback, useEffect, useState } from 'react';
import { CONFIRM_DELETE_DOCUMENT } from '../../constants';
import {
  deleteDocument,
  exportDocumentTables,
  getDocuments,
  getSystemStatus,
  indexAllDocuments,
  previewDocument,
  reindexDocument,
  uploadDocument
} from './documentService';

export function useDocuments({ onOpenPreview }) {
  // Centralize document loading, synchronization, upload, preview, and deletion state.
  const [documents, setDocuments] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [indexingDoc, setIndexingDoc] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [uploadStatus, setUploadStatus] = useState(null);
  const [documentsError, setDocumentsError] = useState(null);
  const [statusError, setStatusError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    // Refresh the inventory and expose fetch failures to the sidebar.
    try {
      setDocuments(await getDocuments());
      setDocumentsError(null);
    } catch (error) {
      console.error('Document fetch failed', error);
      setDocumentsError(error.message);
    }
  }, []);

  useEffect(() => {
    // Load independent status and inventory requests together and ignore results after unmount.
    let active = true;
    Promise.allSettled([getSystemStatus(), getDocuments()]).then(([statusResult, documentsResult]) => {
      if (!active) return;

      if (statusResult.status === 'fulfilled') {
        setSystemStatus(statusResult.value);
        setStatusError(null);
      } else {
        console.error('Status fetch failed', statusResult.reason);
        setStatusError(statusResult.reason.message);
      }

      if (documentsResult.status === 'fulfilled') {
        setDocuments(documentsResult.value);
        setDocumentsError(null);
      } else {
        console.error('Document fetch failed', documentsResult.reason);
        setDocumentsError(documentsResult.reason.message);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const handleIndexAll = useCallback(async () => {
    // Run a repository-wide sync and refresh the visible document list afterward.
    setIndexingDoc(true);
    setUploadStatus('Indexing document chunks into Pinecone...');
    try {
      const data = await indexAllDocuments();
      setUploadStatus(`Indexing successful! Chunks vectorized: ${data.results?.[0]?.chunks_indexed || 'Completed'}`);
    } catch (error) {
      setUploadStatus(`Indexing failed: ${error.message}`);
    } finally {
      setIndexingDoc(false);
      await fetchDocuments();
    }
  }, [fetchDocuments]);

  const handleReindexSingle = useCallback(async (filename) => {
    // Sync one document and report success or failure without changing other rows.
    setActionLoading((previous) => ({ ...previous, [filename]: 'syncing' }));
    try {
      const data = await reindexDocument(filename);
      window.alert(`Successfully synced ${filename} in Pinecone! Chunks indexed: ${data.details?.chunks_indexed || 'Done'}`);
      await fetchDocuments();
    } catch (error) {
      window.alert(`Sync failed: ${error.message}`);
    } finally {
      setActionLoading((previous) => ({ ...previous, [filename]: null }));
    }
  }, [fetchDocuments]);

  const handleDeleteDocument = useCallback(async (filename) => {
    // Confirm destructive removal, then delete the file and reload the inventory.
    if (!window.confirm(CONFIRM_DELETE_DOCUMENT(filename))) return;

    setActionLoading((previous) => ({ ...previous, [filename]: 'deleting' }));
    try {
      await deleteDocument(filename);
      window.alert(`Successfully deleted ${filename} and purged its vectors from Pinecone.`);
      await fetchDocuments();
    } catch (error) {
      window.alert(`Delete failed: ${error.message}`);
    } finally {
      setActionLoading((previous) => ({ ...previous, [filename]: null }));
    }
  }, [fetchDocuments]);

  const handlePreviewDocument = useCallback(async (filename) => {
    // Load parsed document chunks and pass them to the reference inspector.
    setActionLoading((previous) => ({ ...previous, [filename]: 'loading' }));
    try {
      const data = await previewDocument(filename);
      onOpenPreview(data.chunks, `Document Explorer: ${filename}`);
    } catch (error) {
      window.alert(`Preview failed: ${error.message}`);
    } finally {
      setActionLoading((previous) => ({ ...previous, [filename]: null }));
    }
  }, [onOpenPreview]);

  const handleFileUpload = useCallback(async (file) => {
    // Upload and sync the selected file, then refresh the inventory on success.
    if (!file) return;

    setIndexingDoc(true);
    setUploadStatus(`Uploading & syncing ${file.name}...`);
    try {
      await uploadDocument(file);
      setUploadStatus(`Successfully uploaded & synced ${file.name}`);
      await fetchDocuments();
    } catch (error) {
      setUploadStatus(`Upload failed: ${error.message}`);
    } finally {
      setIndexingDoc(false);
    }
  }, [fetchDocuments]);

  const handleExportTables = useCallback(async (filename) => {
    // Fetch the Markdown table export and notify the user if the request fails.
    try {
      return await exportDocumentTables(filename);
    } catch (error) {
      window.alert(`Export failed: ${error.message}`);
      return null;
    }
  }, []);

  return {
    documents,
    systemStatus,
    indexingDoc,
    actionLoading,
    uploadStatus,
    loadError: documentsError || statusError,
    fetchDocuments,
    handleIndexAll,
    handleReindexSingle,
    handleDeleteDocument,
    handlePreviewDocument,
    handleFileUpload,
    handleExportTables
  };
}
