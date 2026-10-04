export const SUGGESTIONS = [
  "Show the full RACI Responsibility Matrix across all phases",
  "What are the mandatory quality testing steps for raw materials?",
  "What parameters must be controlled during high-shear batch mixing?",
  "Explain Phase 4 Packaging, line speed, and secondary bundling procedures"
];

// Build the confirmation prompt with the target filename and deletion side effects.
export const CONFIRM_DELETE_DOCUMENT = (filename) =>
  `Are you sure you want to delete "${filename}"?\n\nThis will remove the file from storage and purge all its vectors from Pinecone.`;