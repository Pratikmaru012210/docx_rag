import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  BookOpen,
  Bot,
  Check,
  Copy,
  Download,
  ExternalLink,
  Layers,
  Send,
  User
} from 'lucide-react';
import { SUGGESTIONS } from '../constants';

export default function ChatView({
  messages,
  inputQuery,
  isStreaming,
  copiedIndex,
  messagesEndRef,
  onSendMessage,
  onInputChange,
  onInputKeyDown,
  onCopy,
  onOpenReferences,
  onDownload
}) {
  // Render the conversation, source controls, and message composer from parent state.
  return (
    <>
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-hero">
            <div className="hero-icon-ring">
              <Layers size={32} color="#818cf8" />
            </div>
            <h2 className="hero-title">FMCG SOP Intelligence Engine</h2>
            <p className="hero-subtitle">
              Ask deep operational questions regarding formulation, RACI accountability,
              raw material procurement, line packaging speeds, or quality compliance.
            </p>
            <div className="suggested-grid">
              {SUGGESTIONS.map((suggestion) => (
                <div key={suggestion} className="suggested-card" onClick={() => onSendMessage(suggestion)}>
                  <span className="suggested-text">{suggestion}</span>
                  <span aria-hidden="true">›</span>
                </div>
              ))}
            </div>
          </div>
        ) : messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`message-row ${message.role}`}>
            <div className={`avatar avatar-${message.role === 'user' ? 'user' : 'ai'}`}>
              {message.role === 'user' ? <User size={18} /> : <Bot size={18} />}
            </div>
            <div className="message-bubble">
              {message.role === 'user' ? (
                <div>{message.content}</div>
              ) : (
                <div>
                  {!message.content && isStreaming && index === messages.length - 1 ? (
                    <div className="thinking-container">
                      <div className="thinking-dots"><span></span><span></span><span></span></div>
                      <span>Analyzing SOP document &amp; generating answer...</span>
                    </div>
                  ) : (
                    <>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                      {isStreaming && index === messages.length - 1 && <span className="typing-cursor" />}
                    </>
                  )}

                  {message.content && !isStreaming && (
                    <div style={{ display: 'flex', gap: '8px', marginTop: '12px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                      <button className="btn btn-secondary" style={{ fontSize: '0.72rem', padding: '4px 8px' }} onClick={() => onCopy(message.content, `msg_${index}`)}>
                        {copiedIndex === `msg_${index}` ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                        {copiedIndex === `msg_${index}` ? 'Copied' : 'Copy Answer'}
                      </button>
                      <button className="btn btn-secondary" style={{ fontSize: '0.72rem', padding: '4px 8px' }} onClick={() => onDownload(`sop_response_${index + 1}.md`, message.content)}>
                        <Download size={12} color="#818cf8" /> Download Answer (.md)
                      </button>
                    </div>
                  )}

                  {message.sources?.length > 0 && (
                    <div style={{ marginTop: '10px' }}>
                      <button className="citation-chip-btn" onClick={() => onOpenReferences(message.sources)} title="Open Reference Inspector to browse cited chunks and tables">
                        <BookOpen size={13} color="#818cf8" />
                        <span>Inspect References &amp; Tables ({message.sources.length} sources)</span>
                        <ExternalLink size={12} style={{ marginLeft: '2px', opacity: 0.8 }} />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-section">
        <div className="input-container">
          <textarea
            className="chat-textarea"
            placeholder="Ask any question about the FMCG Shampoo SOP, RACI tables, testing standards..."
            value={inputQuery}
            onChange={(event) => onInputChange(event.target.value)}
            onKeyDown={onInputKeyDown}
            rows={1}
          />
          <div className="input-actions">
            <button className="send-btn" disabled={!inputQuery.trim() || isStreaming} onClick={() => onSendMessage()}>
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
