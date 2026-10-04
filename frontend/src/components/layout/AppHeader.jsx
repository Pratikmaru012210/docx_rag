import { useRef } from 'react';
import { FolderKanban, MessageSquare, Trash2, UploadCloud } from 'lucide-react';

export default function AppHeader({
  activeTab,
  documentCount,
  hasMessages,
  indexingDoc,
  onTabChange,
  onClearChat,
  onUpload
}) {
  // Provide tab navigation and show actions relevant to the currently selected view.
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    // Clear the input after upload so choosing the same file again still fires a change event.
    onUpload(event.target.files?.[0]);
    event.target.value = '';
  };

  return (
    <header className="chat-header">
      <div className="chat-header-info">
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => onTabChange('chat')}
          >
            <MessageSquare size={15} /> SOP Assistant
          </button>
          <button
            className={`nav-tab ${activeTab === 'docs' ? 'active' : ''}`}
            onClick={() => onTabChange('docs')}
          >
            <FolderKanban size={15} /> Document Management ({documentCount})
          </button>
        </div>
      </div>

      <div className="chat-header-actions">
        {activeTab === 'chat' && hasMessages && (
          <button className="btn btn-secondary" onClick={onClearChat}>
            <Trash2 size={14} /> Clear Chat
          </button>
        )}
        {activeTab === 'docs' && (
          <button
            type="button"
            className="btn btn-primary"
            disabled={indexingDoc}
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud size={14} /> Upload & Sync DOCX
          </button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".docx"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </div>
    </header>
  );
}
