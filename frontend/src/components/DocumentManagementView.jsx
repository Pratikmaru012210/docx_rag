import {
  CheckCircle2,
  FileText,
  FolderKanban,
  HardDrive,
  Layers,
  Table as TableIcon
} from 'lucide-react';
import DocumentActions from './DocumentActions';

export default function DocumentManagementView({
  documents,
  actionLoading,
  onSync,
  onPreview,
  onExportTables,
  onDownload,
  onDelete
}) {
  const totalChunks = documents.reduce((total, document) => total + (document.chunks_count || 0), 0);
  const totalTables = documents.reduce((total, document) => total + (document.tables_count || 0), 0);
  const totalStorageKb = documents.reduce((total, document) => total + (document.size_kb || 0), 0);

  return (
    <div className="doc-hub-view">
      <div className="doc-hub-header">
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ffffff' }}>
            SOP Document Management Hub
          </h2>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
            Manage, preview, update, and selectively sync SOP files in Pinecone vector database with zero wasted embeddings.
          </p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-box" style={{ background: 'rgba(99, 102, 241, 0.15)' }}>
            <FileText size={22} color="#6366f1" />
          </div>
          <div>
            <div className="stat-value">{documents.length}</div>
            <div className="stat-label">Total SOP Documents</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-box" style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
            <Layers size={22} color="#10b981" />
          </div>
          <div>
            <div className="stat-value">{totalChunks}</div>
            <div className="stat-label">Vectorized Chunks</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-box" style={{ background: 'rgba(245, 158, 11, 0.15)' }}>
            <TableIcon size={22} color="#f59e0b" />
          </div>
          <div>
            <div className="stat-value">{totalTables}</div>
            <div className="stat-label">Parsed Tables (RACI / SLAs)</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon-box" style={{ background: 'rgba(168, 85, 247, 0.15)' }}>
            <HardDrive size={22} color="#a855f7" />
          </div>
          <div>
            <div className="stat-value">{totalStorageKb.toFixed(1)} KB</div>
            <div className="stat-label">Total Storage Size</div>
          </div>
        </div>
      </div>

      <div className="data-table-container">
        <div className="data-table-header">
          <span style={{ fontSize: '0.92rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FolderKanban size={16} color="#6366f1" /> Active SOP Document Inventory
          </span>
          <span className="badge badge-success">Incremental Pinecone Sync Active</span>
        </div>

        <div className="data-table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Document Name</th>
                <th>Size</th>
                <th>Chunks</th>
                <th>Tables</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    No documents found in `data/` folder. Click "Upload & Sync DOCX" to add your first SOP!
                  </td>
                </tr>
              ) : documents.map((document) => (
                <tr key={document.filename}>
                  <td style={{ fontWeight: 600, maxWidth: '300px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <FileText size={18} color="#6366f1" style={{ flexShrink: 0 }} />
                      <span style={{ wordBreak: 'break-word' }}>{document.filename}</span>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{document.size_kb} KB</td>
                  <td>
                    <span className="badge badge-indigo">
                      <Layers size={12} color="#818cf8" /> {document.chunks_count || 0} Chunks
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-amber">
                      <TableIcon size={12} color="#fbbf24" /> {document.tables_count || 0} {document.tables_count === 1 ? 'Table' : 'Tables'}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-success">
                      <CheckCircle2 size={12} /> Synced in Pinecone
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <DocumentActions
                      filename={document.filename}
                      loading={actionLoading[document.filename]}
                      showSync
                      showDownload
                      onSync={onSync}
                      onPreview={onPreview}
                      onExportTables={onExportTables}
                      onDownload={onDownload}
                      onDelete={onDelete}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
