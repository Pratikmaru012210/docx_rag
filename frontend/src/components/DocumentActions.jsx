import {
  Download,
  Eye,
  RefreshCw,
  Table as TableIcon,
  Trash2
} from 'lucide-react';

export default function DocumentActions({
  filename,
  loading,
  compact = false,
  showSync = false,
  showDownload = false,
  onPreview,
  onExportTables,
  onDownload,
  onDelete,
  onSync
}) {
  const buttonStyle = compact
    ? { fontSize: '0.7rem', padding: '4px 6px' }
    : { fontSize: '0.76rem', padding: '5px 9px' };

  return (
    <div
      className={compact ? undefined : 'table-actions-cell'}
      style={compact
        ? { display: 'flex', gap: '4px', marginTop: '4px' }
        : { justifyContent: 'flex-end' }}
    >
      {showSync && (
        <button
          className="btn btn-secondary"
          style={buttonStyle}
          onClick={() => onSync(filename)}
          disabled={loading === 'syncing'}
          title="Sync / Update only this document in Pinecone without re-embedding others"
        >
          <RefreshCw size={12} className={loading === 'syncing' ? 'spin' : ''} />
          {loading === 'syncing' ? 'Syncing...' : 'Sync'}
        </button>
      )}
      <button
        className="btn btn-secondary"
        style={compact ? { ...buttonStyle, flex: 1, justifyContent: 'center' } : buttonStyle}
        onClick={() => onPreview(filename)}
        disabled={loading === 'loading'}
        title="Inspect parsed chunks and tables"
      >
        <Eye size={compact ? 11 : 12} /> Inspect
      </button>
      <button
        className="btn btn-secondary"
        style={buttonStyle}
        onClick={() => onExportTables(filename)}
        title="Export all parsed tables to .md"
      >
        <TableIcon size={compact ? 11 : 12} color="#818cf8" />
        {!compact && 'Tables (.md)'}
      </button>
      {showDownload && (
        <button
          className="btn btn-secondary"
          style={buttonStyle}
          onClick={() => onDownload(filename)}
          title="Download original DOCX file"
        >
          <Download size={12} /> DOCX
        </button>
      )}
      <button
        className="btn btn-danger"
        style={buttonStyle}
        onClick={() => onDelete(filename)}
        disabled={loading === 'deleting'}
        title="Delete file and purge its vectors from Pinecone"
      >
        <Trash2 size={compact ? 12 : 12} />
        {!compact && (loading === 'deleting' ? 'Purging...' : 'Delete')}
      </button>
    </div>
  );
}