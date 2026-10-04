import { useCallback, useEffect, useRef, useState } from 'react';
import { streamChatMessage } from './chatService';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const copiedTimeoutRef = useRef(null);
  const chatAbortControllerRef = useRef(null);

  useEffect(() => () => {
    window.clearTimeout(copiedTimeoutRef.current);
    chatAbortControllerRef.current?.abort();
  }, []);

  const handleSendMessage = useCallback(async (queryText = inputQuery) => {
    const trimmed = queryText.trim();
    if (!trimmed || isStreaming) return;

    const history = messages.map(({ role, content }) => ({ role, content }));
    const assistantIndex = messages.length + 1;
    const controller = new AbortController();
    chatAbortControllerRef.current = controller;
    setMessages([
      ...messages,
      { role: 'user', content: trimmed },
      { role: 'assistant', content: '', sources: [] }
    ]);
    setInputQuery('');
    setIsStreaming(true);

    let accumulatedText = '';
    const updateAssistant = (update) => {
      setMessages((previous) => previous.map((message, index) => (
        index === assistantIndex ? { ...message, ...update } : message
      )));
    };

    try {
      await streamChatMessage({
        query: trimmed,
        history,
        signal: controller.signal,
        handlers: {
          onSources: (sources) => updateAssistant({ sources }),
          onToken: (content) => {
            accumulatedText += content;
            updateAssistant({ content: accumulatedText });
          },
          onError: (message) => {
            accumulatedText += `\n\n> ⚠️ Error: ${message}`;
            updateAssistant({ content: accumulatedText });
          }
        }
      });
    } catch (error) {
      if (!controller.signal.aborted) {
        updateAssistant({
          content: `Connection failed: ${error.message}. Please ensure your API keys in .env are configured.`
        });
      }
    } finally {
      if (!controller.signal.aborted) {
        setIsStreaming(false);
        chatAbortControllerRef.current = null;
      }
    }
  }, [inputQuery, isStreaming, messages]);

  const handleKeyDown = useCallback((event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const copyToClipboard = useCallback(async (text, identifier) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(identifier);
      window.clearTimeout(copiedTimeoutRef.current);
      copiedTimeoutRef.current = window.setTimeout(() => setCopiedIndex(null), 2000);
    } catch (error) {
      console.error('Clipboard copy failed', error);
      window.alert(`Unable to copy to clipboard: ${error.message}`);
    }
  }, []);

  const clearChat = useCallback(() => setMessages([]), []);

  return {
    messages,
    inputQuery,
    setInputQuery,
    isStreaming,
    copiedIndex,
    handleSendMessage,
    handleKeyDown,
    copyToClipboard,
    clearChat
  };
}
