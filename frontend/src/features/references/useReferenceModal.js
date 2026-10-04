import { useCallback, useEffect, useState } from 'react';
import { downloadMarkdownFile } from '../../shared/utils/downloadMarkdownFile';

export function useReferenceModal() {
  const [sources, setSources] = useState(null);
  const [sourceIndex, setSourceIndex] = useState(0);
  const [title, setTitle] = useState(null);

  const openModal = useCallback((nextSources, nextTitle = null) => {
    setSources(nextSources);
    setSourceIndex(0);
    setTitle(nextTitle);
  }, []);

  const closeModal = useCallback(() => {
    setSources(null);
    setSourceIndex(0);
    setTitle(null);
  }, []);

  const handlePrevSource = useCallback(() => {
    setSourceIndex((previous) => Math.max(0, previous - 1));
  }, []);

  const handleNextSource = useCallback(() => {
    setSourceIndex((previous) => Math.min((sources?.length || 1) - 1, previous + 1));
  }, [sources]);

  useEffect(() => {
    if (!sources) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') closeModal();
      if (event.key === 'ArrowLeft') handlePrevSource();
      if (event.key === 'ArrowRight') handleNextSource();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeModal, handleNextSource, handlePrevSource, sources]);

  const downloadAllSources = useCallback(() => {
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
