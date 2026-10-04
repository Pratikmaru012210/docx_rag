import { useEffect, useRef, useState } from 'react';
import AppHeader from './components/layout/AppHeader';
import AppSidebar from './components/layout/AppSidebar';
import ChatView from './components/ChatView';
import DocumentManagementView from './components/DocumentManagementView';
import ReferenceModal from './components/ReferenceModal';
import { useChat } from './features/chat/useChat';
import { useDocuments } from './features/documents/useDocuments';
import { useReferenceModal } from './features/references/useReferenceModal';
import { downloadMarkdownFile } from './shared/utils/downloadMarkdownFile';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const messagesEndRef = useRef(null);
  const modal = useReferenceModal();
  const chat = useChat();
  const documents = useDocuments({ onOpenPreview: modal.openModal });

  useEffect(() => {
    if (activeTab === 'chat') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activeTab, chat.messages, chat.isStreaming]);

  const handleExportTables = async (filename) => {
    const data = await documents.handleExportTables(filename);
    if (data) downloadMarkdownFile(data.filename, data.content);
  };

  const handleDownloadDocx = (filename) => {
    window.open(`/api/documents/${encodeURIComponent(filename)}/download-docx`, '_blank');
  };

  return (
    <div className="app-container">
      <AppSidebar
        documents={documents.documents}
        actionLoading={documents.actionLoading}
        systemStatus={documents.systemStatus}
        indexingDoc={documents.indexingDoc}
        uploadStatus={documents.uploadStatus}
        loadError={documents.loadError}
        onIndexAll={documents.handleIndexAll}
        onUpload={documents.handleFileUpload}
        onPreview={documents.handlePreviewDocument}
        onExportTables={handleExportTables}
        onDelete={documents.handleDeleteDocument}
      />

      <main className="chat-main">
        <AppHeader
          activeTab={activeTab}
          documentCount={documents.documents.length}
          hasMessages={chat.messages.length > 0}
          indexingDoc={documents.indexingDoc}
          onTabChange={setActiveTab}
          onClearChat={chat.clearChat}
          onUpload={documents.handleFileUpload}
        />

        {activeTab === 'chat' && (
          <ChatView
            messages={chat.messages}
            inputQuery={chat.inputQuery}
            isStreaming={chat.isStreaming}
            copiedIndex={chat.copiedIndex}
            messagesEndRef={messagesEndRef}
            onSendMessage={chat.handleSendMessage}
            onInputChange={chat.setInputQuery}
            onInputKeyDown={chat.handleKeyDown}
            onCopy={chat.copyToClipboard}
            onOpenReferences={(sources) => modal.openModal(sources)}
            onDownload={downloadMarkdownFile}
          />
        )}

        {activeTab === 'docs' && (
          <DocumentManagementView
            documents={documents.documents}
            actionLoading={documents.actionLoading}
            onSync={documents.handleReindexSingle}
            onPreview={documents.handlePreviewDocument}
            onExportTables={handleExportTables}
            onDownload={handleDownloadDocx}
            onDelete={documents.handleDeleteDocument}
          />
        )}
      </main>

      {modal.sources && modal.currentSource && (
        <ReferenceModal
          sources={modal.sources}
          sourceIndex={modal.sourceIndex}
          currentSource={modal.currentSource}
          title={modal.title}
          copiedIndex={chat.copiedIndex}
          onClose={modal.closeModal}
          onPrevious={modal.handlePrevSource}
          onNext={modal.handleNextSource}
          onCopy={chat.copyToClipboard}
          onDownload={downloadMarkdownFile}
          onDownloadAll={modal.downloadAllSources}
        />
      )}
    </div>
  );
}
