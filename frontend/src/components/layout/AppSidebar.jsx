import { useRef } from 'react';
import {
  Bot,
  CheckCircle2,
  Database,
  FileText,
  RefreshCw,
  Sparkles,
  UploadCloud
} from 'lucide-react';
import DocumentActions from '../DocumentActions';

export default function AppSidebar({
  documents,
  actionLoading,
  systemStatus,
  indexingDoc,
  uploadStatus,
  loadError,
  onIndexAll,
  onUpload,
  onPreview,
  onExportTables,
  onDelete
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    onUpload(event.target.files?.[0]);
    event.target.value = '';
  };

  return (
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
        <div className="sidebar-quick-actions">
          <div className="section-label">Vector Store Actions</div>
          <button
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={onIndexAll}
            disabled={indexingDoc}
          >
            <RefreshCw size={14} className={indexingDoc ? 'spin' : ''} />
            {indexingDoc ? 'Vectorizing SOP Chunks...' : 'Sync All Documents'}
          </button>
        </div>

        <button
          type="button"
          className="dropzone"
          onClick={() => fileInputRef.current?.click()}
          disabled={indexingDoc}
        >
          <UploadCloud size={24} color="#94a3b8" />
          <span className="dropzone-text">Click to upload new DOCX SOP</span>
          <span className="dropzone-hint">Preserves tables & incremental sync</span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".docx"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {uploadStatus && <div className="sidebar-feedback">{uploadStatus}</div>}
        {loadError && <div className="sidebar-feedback sidebar-feedback-error">{loadError}</div>}

        <div className="sidebar-repository">
          <div className="section-label">
            <span>SOP Repository</span>
            <span className="badge badge-success">{documents.length} Files</span>
          </div>

          <div className="document-list">
            {documents.map((document) => (
              <div key={document.filename} className="doc-card" title={document.filename}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, width: '100%' }}>
                  <FileText size={16} color="#6366f1" style={{ flexShrink: 0 }} />
                  <div className="doc-name" title={document.filename}>{document.filename}</div>
                </div>
                <div className="doc-meta">
                  <span>{document.size_kb} KB • {document.chunks_count || 0} chunks</span>
                  <span className="badge badge-success">
                    <CheckCircle2 size={11} /> Vectorized
                  </span>
                </div>
                <DocumentActions
                  filename={document.filename}
                  compact
                  loading={actionLoading[document.filename]}
                  onPreview={onPreview}
                  onExportTables={onExportTables}
                  onDelete={onDelete}
                />
              </div>
            ))}
          </div>
        </div>
      </div>

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
            {systemStatus?.groq_configured
              ? systemStatus.groq_model?.split('/').pop()?.toUpperCase() || 'Configured'
              : 'Set Key'}
          </span>
        </div>
      </div>
    </aside>
  );
}
