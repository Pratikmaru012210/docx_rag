import os
from typing import Any, Dict, List

from fastapi import UploadFile

from backend.config import settings
from backend.constants import ERROR_DOCX_ONLY, ERROR_FILE_NOT_FOUND, ERROR_NO_TABLES
from backend.file_utils import resolve_document_path, save_document_atomically
from backend.parser import HierarchicalDocxParser
from backend.services.vector_store import VectorStoreService


class DocumentService:
    """Orchestrates document file management, parsing, vector store synchronization, and table exports."""

    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.parser = HierarchicalDocxParser()

    def list_documents(self) -> List[Dict[str, Any]]:
        """Scans the data repository and returns metadata for each SOP file."""
        if not os.path.exists(settings.DATA_DIR):
            return []

        files = []
        for fname in os.listdir(settings.DATA_DIR):
            if fname.endswith(".docx") or fname.endswith(".doc"):
                fpath = os.path.join(settings.DATA_DIR, fname)
                size_kb = round(os.path.getsize(fpath) / 1024, 2)
                modified = os.path.getmtime(fpath)

                try:
                    chunks = self.parser.create_chunks(fpath)
                    chunks_count = len(chunks)
                    tables_count = sum(
                        1 for c in chunks if c["content_type"] == "table"
                    )
                except Exception:
                    chunks_count = 0
                    tables_count = 0

                files.append(
                    {
                        "filename": fname,
                        "size_kb": size_kb,
                        "modified": modified,
                        "chunks_count": chunks_count,
                        "tables_count": tables_count,
                    }
                )
        return files

    def get_document_path(self, filename: str) -> str:
        try:
            fpath = resolve_document_path(settings.DATA_DIR, filename)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"{ERROR_FILE_NOT_FOUND}: {filename}")
        return fpath

    def save_uploaded_file(self, file: UploadFile) -> str:
        """Saves an uploaded DOCX file to the data repository."""
        if not file.filename or not file.filename.endswith(".docx"):
            raise ValueError(ERROR_DOCX_ONLY)

        target_path = save_document_atomically(settings.DATA_DIR, file.filename, file.file)
        return target_path

    def sync_document(self, filename: str) -> Dict[str, Any]:
        """Indexes/re-indexes a single document incrementally without touching others."""
        fpath = self.get_document_path(filename)
        doc_name = os.path.basename(fpath)

        # Parse and embed before replacing existing vectors, so failed preparation preserves the current index.
        chunks = self.parser.create_chunks(fpath)
        count = self.vector_store.replace_document_chunks(doc_name, chunks)
        table_count = sum(1 for c in chunks if c["content_type"] == "table")

        return {
            "status": "success" if chunks else "warning",
            "document": doc_name,
            "chunks_indexed": count,
            "table_chunks": table_count,
        }

    def sync_all_documents(self) -> List[Dict[str, Any]]:
        """Indexes all DOCX documents in the data directory."""
        results = []
        for doc_info in self.list_documents():
            fname = doc_info["filename"]
            try:
                res = self.sync_document(fname)
                results.append(res)
            except Exception as e:
                results.append({"document": fname, "status": "error", "error": str(e)})
        return results

    def delete_document(self, filename: str) -> Dict[str, Any]:
        """Deletes file locally and purges its vectors from Pinecone."""
        fpath = self.get_document_path(filename)
        vector_status = self.vector_store.delete_document_vectors(filename)
        os.remove(fpath)
        return {
            "status": "success",
            "filename": filename,
            "message": f"Successfully deleted {filename} and purged its vectors from Pinecone.",
            "vector_status": vector_status,
        }

    def get_document_preview(self, filename: str) -> Dict[str, Any]:
        """Returns structured elements and chunks for a document."""
        fpath = self.get_document_path(filename)
        chunks = self.parser.create_chunks(fpath)
        return {
            "filename": filename,
            "total_chunks": len(chunks),
            "table_chunks": sum(1 for c in chunks if c["content_type"] == "table"),
            "chunks": chunks,
        }

    def export_document_tables(self, filename: str) -> Dict[str, Any]:
        """Extracts all tables from a document and compiles them into a markdown document."""
        fpath = self.get_document_path(filename)
        chunks = self.parser.create_chunks(fpath)
        table_chunks = [c for c in chunks if c["content_type"] == "table"]

        if not table_chunks:
            raise ValueError(ERROR_NO_TABLES)

        md_output = [f"# Extracted Tables Reference: {filename}\n"]
        for i, t in enumerate(table_chunks, 1):
            md_output.append(f"## Table {i}: {t['breadcrumb']}\n")
            md_output.append(t["raw_content"] + "\n\n---\n")

        full_md = "\n".join(md_output)
        return {
            "filename": f"{os.path.splitext(filename)[0]}_tables.md",
            "content": full_md,
            "tables_count": len(table_chunks),
        }
