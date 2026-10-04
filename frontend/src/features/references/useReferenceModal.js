import { useCallback, useEffect, useState } from 'react';
import { downloadMarkdownFile } from '../../shared/utils/downloadMarkdownFile';

export function useReferenceModal() {
  // Track the active citation and expose bounded navigation and export actions.
  const [sources, setSources] = useState(null);
  const [sourceIndex, setSourceIndex] = useState(0);
  const [title, setTitle] = useState(null);

  const openModal = useCallback((nextSources, nextTitle = null) => {
    // Open the inspector at the first citation with its optional title.
    setSources(nextSources);
    setSourceIndex(0);
    setTitle(nextTitle);
  }, []);

  const closeModal = useCallback(() => {
    // Clear the current citation set and reset modal navigation state.
    setSources(null);
    setSourceIndex(0);
    setTitle(null);
  }, []);

  const handlePrevSource = useCallback(() => {
    // Move backward without allowing the selected source index to become negative.
    setSourceIndex((previous) => Math.max(0, previous - 1));
  }, []);

  const handleNextSource = useCallback(() => {
    // Move forward while clamping the index to the last available source.
    setSourceIndex((previous) => Math.min((sources?.length || 1) - 1, previous + 1));
  }, [sources]);

  useEffect(() => {
    // Enable keyboard navigation only while citations are open and remove listeners on cleanup.
    if (!sources) return undefined;

    const handleKeyDown = (event) => {
      // Map Escape and arrow keys to the same close/navigation actions as the dialog buttons.
      if (event.key === 'Escape') closeModal();
      if (event.key === 'ArrowLeft') handlePrevSource();
      if (event.key === 'ArrowRight') handleNextSource();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeModal, handleNextSource, handlePrevSource, sources]);

  const downloadAllSources = useCallback(() => {
    // Combine the current citations into one Markdown download.
    if (!sources) return;

    const combined = sources
      .map((source, index) => (
        `# Reference ${index + 1}: ${source.breadcrumb}\n**Type:** ${source.content_type} | **Score:** ${source.score ? `${(source.score * 100).toFixed(1)}%` : 'Document Chunk'}\n\n${source.raw_content || source.text}`
      ))
      .join('\n\n---\n\n');
    downloadMarkdownFile('all_verified_references.md', combined);
  }, [sources]);

  return {
    sources,
    sourceIndex,
    currentSource: sources?.[sourceIndex] || null,
    title,
    openModal,
    closeModal,
    handlePrevSource,
    handleNextSource,
    downloadAllSources
  };
}
