import os
from typing import List, Dict, Any, Generator, Optional
from groq import Groq
from backend.parser import HierarchicalDocxParser
from backend.config import settings
from backend.constants import SYSTEM_INSTRUCTION_SOP, ERROR_GROQ_KEY_MISSING
from backend.services.vector_store import VectorStoreService


class RAGService:
    def __init__(self, vector_store: Optional[VectorStoreService] = None):
        """Set up document parsing, vector storage, and lazy Groq client configuration."""
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.vector_store = vector_store or VectorStoreService()

        self.parser = HierarchicalDocxParser(
            max_chunk_words=settings.MAX_CHUNK_WORDS,
            overlap_words=settings.CHUNK_OVERLAP_WORDS
        )

        self._groq: Optional[Groq] = None

    def get_groq_client(self) -> Groq:
        """Create the Groq client only when first needed, after validating its key."""
        if not self._groq:
            if not self.groq_api_key:
                raise ValueError(ERROR_GROQ_KEY_MISSING)
            self._groq = Groq(api_key=self.groq_api_key)
        return self._groq

    def delete_document_vectors(self, doc_name: str) -> Dict[str, Any]:
        """Deletes all vector chunks associated with a specific document from Pinecone."""
        return self.vector_store.delete_document_vectors(doc_name)

    def index_document(self, file_path: str, purge_existing: bool = True) -> Dict[str, Any]:
        """Parses DOCX file hierarchically and indexes chunks into Pinecone (replaces old vectors of this doc)."""
        doc_name = os.path.basename(file_path)
        chunks = self.parser.create_chunks(file_path)
        if not purge_existing:
            count = self.vector_store.upsert_chunks(doc_name, chunks)
        else:
            count = self.vector_store.replace_document_chunks(doc_name, chunks)

        if not chunks:
            return {
                "status": "warning",
                "document": doc_name,
                "message": "No content found in document",
                "chunks_indexed": 0,
                "table_chunks": 0,
            }

        return {
            "status": "success",
            "document": doc_name,
            "chunks_indexed": count,
            "table_chunks": sum(1 for c in chunks if c["content_type"] == "table")
        }

    def retrieve_context(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieves top-k context chunks from Pinecone vector DB."""
        return self.vector_store.similarity_search(query, top_k=top_k)

    def build_prompt(self, query: str, context_chunks: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Builds system prompt and context augmented conversation for Groq."""
        # Keep each retrieved chunk labeled so the model can distinguish its source and section.
        context_blocks = []
        for i, c in enumerate(context_chunks, 1):
            context_blocks.append(
                f"### [Source #{i}] - {c['breadcrumb']} ({c['content_type'].upper()})\n"
                f"{c['text']}"
            )
        combined_context = "\n\n---\n\n".join(context_blocks)

        user_content = (
            f"Retrieved Document Context:\n"
            f"```\n{combined_context}\n```\n\n"
            f"User Question:\n{query}"
        )

        messages = [{"role": "system", "content": SYSTEM_INSTRUCTION_SOP}]

        # Limit history to the most recent four messages to bound prompt size.
        if chat_history:
            for msg in chat_history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_content})
        return messages

    def stream_chat(self, query: str, chat_history: List[Dict[str, str]] = None, top_k: int = 4) -> Generator[Dict[str, Any], None, None]:
        """
        Streams answers from Groq with source citation metadata sent upfront.
        Yields events:
        - {"type": "sources", "sources": [...]}
        - {"type": "token", "content": "..."}
        - {"type": "done"}
        """
        groq = self.get_groq_client()
        context_chunks = self.retrieve_context(query, top_k=top_k)

        # Yield sources first so the UI can immediately display citations & allow markdown download
        yield {
            "type": "sources",
            "sources": [
                {
                    "chunk_id": c["chunk_id"],
                    "breadcrumb": c["breadcrumb"],
                    "content_type": c["content_type"],
                    "score": round(c["score"], 3),
                    "text": c["text"],
                    "raw_content": c.get("raw_content", c["text"]),
                    "preview": c["text"][:250] + ("..." if len(c["text"]) > 250 else "")
                }
                for c in context_chunks
            ]
        }

        messages = self.build_prompt(query, context_chunks, chat_history)
        stream = groq.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=0.2,
            max_tokens=2048,
            stream=True
        )

        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield {"type": "token", "content": token}

        yield {"type": "done"}
