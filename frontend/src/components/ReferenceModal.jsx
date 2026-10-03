import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Copy,
  Download,
  FileText,
  Table as TableIcon,
  X
} from 'lucide-react';

export default function ReferenceModal({
  sources,
  sourceIndex,
  currentSource,
  title,
  copiedIndex,
  onClose,
  onPrevious,
  onNext,
  onCopy,
  onDownload,
  onDownloadAll
}) {
  if (!sources || !currentSource) return null;

  const content = currentSource.raw_content || currentSource.text;
  const copyId = `modal_copy_${sourceIndex}`;

  return (
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="modal-card">
        <div className="modal-header">
          <div className="modal-header-left">
            <div className="modal-title-row">
              <span className="modal-title">
                {currentSource.content_type === 'table' ? (
                  <TableIcon size={18} color="#6366f1" />
                ) : (
                  <FileText size={18} color="#6366f1" />
                )}
                {title || 'Reference Inspector'}
              </span>
              <span className="badge badge-success">
                {currentSource.content_type?.toUpperCase()} {currentSource.score ? `• ${(currentSource.score * 100).toFixed(1)}% match` : ''}
              </span>
              <span className="nav-counter">{sourceIndex + 1} of {sources.length}</span>
            </div>
            <div className="modal-breadcrumb" title={currentSource.breadcrumb}>
              📍 {currentSource.breadcrumb}
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close (Esc)">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="modal-markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        </div>

        <div className="modal-footer">
          <div className="modal-nav-group">
            <button className="btn btn-secondary" onClick={onPrevious} disabled={sourceIndex === 0} title="Previous Reference (Left Arrow)">
              <ChevronLeft size={15} /> Prev
            </button>
            <button className="btn btn-secondary" onClick={onNext} disabled={sourceIndex === sources.length - 1} title="Next Reference (Right Arrow)">
              Next <ChevronRight size={15} />
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button className="btn btn-secondary" onClick={() => onCopy(content, copyId)}>
              {copiedIndex === copyId ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
              {copiedIndex === copyId ? 'Copied' : 'Copy Markdown'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => onDownload(
                `${currentSource.content_type === 'table' ? 'table_ref' : 'chunk_ref'}_${sourceIndex + 1}.md`,
                `# Reference: ${currentSource.breadcrumb}\n**Type:** ${currentSource.content_type}\n\n---\n\n${content}`
              )}
            >
              <Download size={13} color="#818cf8" /> Export This (.md)
            </button>
            {sources.length > 1 && (
              <button className="btn btn-primary" onClick={onDownloadAll}>
                <Download size={13} /> Export All ({sources.length})
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
