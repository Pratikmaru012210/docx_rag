import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Database,
  Sparkles,
  Bot,
  RefreshCw,
  CheckCircle2,
  Trash2,
  MessageSquare,
  FolderKanban
} from 'lucide-react';
import DocumentActions from './components/DocumentActions';
import DocumentManagementView from './components/DocumentManagementView';
import ReferenceModal from './components/ReferenceModal';
import { CONFIRM_DELETE_DOCUMENT } from './constants';
import ChatView from './components/ChatView';

// Helper: Download text string as a .md file
const downloadMarkdownFile = (filename, content) => {
  const element = document.createElement("a");
  const file = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  element.href = URL.createObjectURL(file);
  element.download = filename.endsWith('.md') ? filename : `${filename}.md`;
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
};

export default function App() {
  // Navigation: 'chat' | 'docs'
  const [activeTab, setActiveTab] = useState('chat');

  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [indexingDoc, setIndexingDoc] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [uploadStatus, setUploadStatus] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Modal State for References & Structure Viewer
  const [activeModalSources, setActiveModalSources] = useState(null); // Array of sources or null
  const [activeSourceIndex, setActiveSourceIndex] = useState(0);
  const [modalTitleOverride, setModalTitleOverride] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const hubFileInputRef = useRef(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom();
    }
  }, [messages, isStreaming, activeTab]);

  // Fetch initial documents and status
  useEffect(() => {
    fetchStatus();
    fetchDocuments();
  }, []);

  // Keyboard navigation for Modal (Esc, Left Arrow, Right Arrow)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!activeModalSources) return;

      if (e.key === 'Escape') {
        setActiveModalSources(null);
        setActiveSourceIndex(0);
        setModalTitleOverride(null);
      } else if (e.key === 'ArrowLeft') {
        setActiveSourceIndex((index) => Math.max(0, index - 1));
      } else if (e.key === 'ArrowRight') {
        setActiveSourceIndex((index) => Math.min(activeModalSources.length - 1, index + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeModalSources]);

  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
      }
    } catch (err) {
      console.error("Status fetch failed", err);
    }
  }

  async function fetchDocuments() {
    try {
      const res = await fetch('/api/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error("Doc fetch failed", err);
    }
  }

  // Re-index all documents
  const handleIndexAll = async () => {
    setIndexingDoc(true);
    setUploadStatus("Indexing document chunks into Pinecone...");
    try {
      const res = await fetch('/api/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus(`Indexing successful! Chunks vectorized: ${data.results?.[0]?.chunks_indexed || 'Completed'}`);
      } else {
        setUploadStatus(`Indexing error: ${data.detail || 'Failed'}`);
      }
    } catch (err) {
      setUploadStatus(`Indexing failed: ${err.message}`);
    } finally {
      setIndexingDoc(false);
      fetchDocuments();
    }
  };

  // Single Document Sync / Re-index (Updates only this doc, saves costs)
  const handleReindexSingle = async (filename) => {
    setActionLoading(prev => ({ ...prev, [filename]: 'syncing' }));
    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}/reindex`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Successfully synced ${filename} in Pinecone! Chunks indexed: ${data.details?.chunks_indexed || 'Done'}`);
        fetchDocuments();
      } else {
        alert(`Sync error: ${data.detail || 'Failed'}`);
      }
    } catch (err) {
      alert(`Sync failed: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [filename]: null }));
    }
  };

  // Single Document Delete (Deletes file locally + purges vectors in Pinecone)
  const handleDeleteDocument = async (filename) => {
    if (!window.confirm(CONFIRM_DELETE_DOCUMENT(filename))) {
      return;
    }

    setActionLoading(prev => ({ ...prev, [filename]: 'deleting' }));
    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Successfully deleted ${filename} and purged its vectors from Pinecone.`);
        fetchDocuments();
      } else {
        alert(`Delete failed: ${data.detail || 'Error'}`);
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [filename]: null }));
    }
  };

  // Preview Parsed Structure of Document in Modal
  const handlePreviewDocument = async (filename) => {
    setActionLoading(prev => ({ ...prev, [filename]: 'loading' }));
    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}/preview`);
      if (res.ok) {
        const data = await res.json();
        setModalTitleOverride(`Document Explorer: ${filename}`);
        openModalWithSources(data.chunks, 0);
      } else {
        alert("Failed to load document preview.");
      }
    } catch (err) {
      alert(`Preview error: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [filename]: null }));
    }
  };

  // Download raw DOCX
  const handleDownloadDocx = (filename) => {
    window.open(`/api/documents/${encodeURIComponent(filename)}/download-docx`, '_blank');
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setIndexingDoc(true);
    setUploadStatus(`Uploading & syncing ${file.name}...`);
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus(`Successfully uploaded & synced ${file.name}`);
        fetchDocuments();
      } else {
        setUploadStatus(`Upload failed: ${data.detail}`);
      }
    } catch (err) {
      setUploadStatus(`Upload error: ${err.message}`);
    } finally {
      setIndexingDoc(false);
    }
  };

  const downloadDocumentTables = async (filename) => {
    try {
      const res = await fetch(`/api/export-tables?filename=${encodeURIComponent(filename)}`);
      if (res.ok) {
        const data = await res.json();
        downloadMarkdownFile(data.filename, data.content);
      } else {
        alert("No tables found in this document to export.");
      }
    } catch (err) {
      alert(`Export error: ${err.message}`);
    }
  };

  const copyToClipboard = (text, identifier) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(identifier);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Modal navigation handlers
  const openModalWithSources = (sourcesList, initialIndex = 0) => {
    setActiveModalSources(sourcesList);
    setActiveSourceIndex(initialIndex);
  };

  const closeModal = () => {
    setActiveModalSources(null);
    setActiveSourceIndex(0);
    setModalTitleOverride(null);
  };

  const handlePrevSource = () => {
    if (!activeModalSources) return;
    setActiveSourceIndex((prev) => (prev > 0 ? prev - 1 : prev));
  };

  const handleNextSource = () => {
    if (!activeModalSources) return;
    setActiveSourceIndex((prev) => (prev < activeModalSources.length - 1 ? prev + 1 : prev));
  };

  const downloadAllModalSources = () => {
    if (!activeModalSources) return;
    const combined = activeModalSources
      .map((src, i) => `# Reference ${i + 1}: ${src.breadcrumb}\n**Type:** ${src.content_type} | **Score:** ${src.score ? (src.score * 100).toFixed(1) + '%' : 'Document Chunk'}\n\n${src.raw_content || src.text}`)
      .join('\n\n---\n\n');
    downloadMarkdownFile('all_verified_references.md', combined);
  };

  const handleSendMessage = async (queryText = inputQuery) => {
    const trimmed = queryText.trim();
    if (!trimmed || isStreaming) return;

    const userMessage = { role: 'user', content: trimmed };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputQuery('');
    setIsStreaming(true);

    // Placeholder assistant message
    const assistantIndex = newMessages.length;
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [] }]);

    try {
      const historyPayload = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: trimmed,
          history: historyPayload,
          top_k: 4
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulatedText = '';
      let messageSources = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const rawChunk = decoder.decode(value, { stream: true });
        const lines = rawChunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'sources') {
                messageSources = data.sources;
                setMessages((previous) => previous.map((message, index) => (
                  index === assistantIndex ? { ...message, sources: messageSources } : message
                )));
              } else if (data.type === 'token') {
                accumulatedText += data.content;
                setMessages((previous) => previous.map((message, index) => (
                  index === assistantIndex ? { ...message, content: accumulatedText } : message
                )));
              } else if (data.type === 'error') {
                accumulatedText += `\n\n> ⚠️ Error: ${data.message}`;
                setMessages((previous) => previous.map((message, index) => (
                  index === assistantIndex ? { ...message, content: accumulatedText } : message
                )));
              }
            } catch {
              // Ignore partial JSON parse errors in chunk stream
            }
          }
        }
      }
    } catch (err) {
      setMessages((previous) => previous.map((message, index) => (
        index === assistantIndex
          ? { ...message, content: `Connection failed: ${err.message}. Please ensure your API keys in .env are configured.` }
          : message
      )));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const currentModalSource = activeModalSources ? activeModalSources[activeSourceIndex] : null;

  return (
    <div className="app-container">
      {/* Sidebar: Repository & Quick Actions */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-badge">
            <div className="brand-icon">
              <Sparkles size={20} color="#ffffff" />
            </div>
            <div>
              <h1 className="brand-title">SOP Intelligence</h1>
              <span className="brand-subtitle">FMCG Operations RAG</span>
            </div>
          </div>
        </div>

        <div className="sidebar-content">
          {/* Document Repository list */}
          <div>
            <div className="section-label">
              <span>SOP Repository</span>
              <span className="badge badge-success">{documents.length} Files</span>
            </div>

            {documents.map((doc, idx) => (
              <div key={idx} className="doc-card" title={doc.filename}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, width: '100%' }}>
                  <FileText size={16} color="#6366f1" style={{ flexShrink: 0 }} />
                  <div className="doc-name" title={doc.filename}>{doc.filename}</div>
                </div>
                <div className="doc-meta">
                  <span>{doc.size_kb} KB • {doc.chunks_count || 0} chunks</span>
                  <span className="badge badge-success">
                    <CheckCircle2 size={11} /> Vectorized
                  </span>
                </div>
                <DocumentActions
                  filename={doc.filename}
                  compact
                  loading={actionLoading[doc.filename]}
                  onPreview={handlePreviewDocument}
                  onExportTables={downloadDocumentTables}
                  onDelete={handleDeleteDocument}
                />
              </div>
            ))}

            {/* Dropzone for Uploads */}
            <div
              className="dropzone"
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud size={24} color="#94a3b8" />
              <span className="dropzone-text">Click to upload new DOCX SOP</span>
              <span className="dropzone-hint">Preserves tables & incremental sync</span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".docx"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
              />
            </div>

            {uploadStatus && (
              <div style={{
                marginTop: '10px',
                fontSize: '0.74rem',
                padding: '8px 10px',
                borderRadius: '6px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                color: '#cbd5e1'
              }}>
                {uploadStatus}
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div>
            <div className="section-label">Vector Store Actions</div>
            <button
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={handleIndexAll}
              disabled={indexingDoc}
            >
              <RefreshCw size={14} className={indexingDoc ? "spin" : ""} />
              {indexingDoc ? "Vectorizing SOP Chunks..." : "Sync All Documents"}
            </button>
          </div>
        </div>

        {/* Sidebar Footer / System Status */}
        <div className="sidebar-footer">
          <div className="status-pill">
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Database size={13} /> Pinecone DB
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span className={`status-indicator ${systemStatus?.pinecone_configured ? '' : 'offline'}`}></span>
              {systemStatus?.pinecone_configured ? 'Ready' : 'Set Key'}
            </span>
          </div>

          <div className="status-pill">
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Bot size={13} /> Groq LLM
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span className={`status-indicator ${systemStatus?.groq_configured ? '' : 'offline'}`}></span>
              {systemStatus?.groq_configured ? 'Llama-3.3' : 'Set Key'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="chat-main">
        {/* Top Header & Navigation Tabs */}
        <header className="chat-header">
          <div className="chat-header-info">
            <div className="nav-tabs">
              <button
                className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
                onClick={() => setActiveTab('chat')}
              >
                <MessageSquare size={15} /> SOP Assistant
              </button>
              <button
                className={`nav-tab ${activeTab === 'docs' ? 'active' : ''}`}
                onClick={() => setActiveTab('docs')}
              >
                <FolderKanban size={15} /> Document Management ({documents.length})
              </button>
            </div>
          </div>

          <div className="chat-header-actions">
            {activeTab === 'chat' && messages.length > 0 && (
              <button className="btn btn-secondary" onClick={clearChat}>
                <Trash2 size={14} /> Clear Chat
              </button>
            )}
            {activeTab === 'docs' && (
              <button
                className="btn btn-primary"
                onClick={() => hubFileInputRef.current?.click()}
                disabled={indexingDoc}
              >
                <UploadCloud size={14} /> Upload & Sync DOCX
                <input
                  ref={hubFileInputRef}
                  type="file"
                  accept=".docx"
                  style={{ display: 'none' }}
                  onChange={handleFileUpload}
                />
              </button>
            )}
          </div>
        </header>

        {/* ==========================================================
            VIEW 1: Interactive RAG Chatbot
            ========================================================== */}
        {activeTab === 'chat' && (
          <ChatView
            messages={messages}
            inputQuery={inputQuery}
            isStreaming={isStreaming}
            copiedIndex={copiedIndex}
            messagesEndRef={messagesEndRef}
            onSendMessage={handleSendMessage}
            onInputChange={setInputQuery}
            onInputKeyDown={handleKeyDown}
            onCopy={copyToClipboard}
            onOpenReferences={(sources) => {
              setModalTitleOverride(null);
              openModalWithSources(sources, 0);
            }}
            onDownload={downloadMarkdownFile}
          />
        )}

        {/* ==========================================================
            VIEW 2: Dedicated Document Management Hub (CRUD Operations)
            ========================================================== */}
        {activeTab === 'docs' && (
          <DocumentManagementView
            documents={documents}
            actionLoading={actionLoading}
            onSync={handleReindexSingle}
            onPreview={handlePreviewDocument}
            onExportTables={downloadDocumentTables}
            onDownload={handleDownloadDocx}
            onDelete={handleDeleteDocument}
          />
        )}
      </main>

      {/* ==========================================================
          Interactive Reference & Structure Inspector Modal
          ========================================================== */}
      {activeModalSources && currentModalSource && (
        <ReferenceModal
          sources={activeModalSources}
          sourceIndex={activeSourceIndex}
          currentSource={currentModalSource}
          title={modalTitleOverride}
          copiedIndex={copiedIndex}
          onClose={closeModal}
          onPrevious={handlePrevSource}
          onNext={handleNextSource}
          onCopy={copyToClipboard}
          onDownload={downloadMarkdownFile}
          onDownloadAll={downloadAllModalSources}
        />
      )}
    </div>
  );
}
