import time
from typing import List, Dict, Any, Generator, Optional
from pinecone import Pinecone, ServerlessSpec
from groq import Groq
from backend.parser import HierarchicalDocxParser
from backend.config import settings
from backend.constants import SYSTEM_INSTRUCTION_SOP, ERROR_PINECONE_KEY_MISSING, ERROR_GROQ_KEY_MISSING


class RAGService:
    def __init__(self):
        self.pinecone_api_key = settings.PINECONE_API_KEY
        self.pinecone_index_name = settings.PINECONE_INDEX_NAME
        self.pinecone_cloud = settings.PINECONE_CLOUD
        self.pinecone_region = settings.PINECONE_REGION
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

        self.parser = HierarchicalDocxParser(
            max_chunk_words=settings.MAX_CHUNK_WORDS,
            overlap_words=settings.CHUNK_OVERLAP_WORDS
        )

        self._pc: Optional[Pinecone] = None
        self._groq: Optional[Groq] = None
        self._index = None

    def get_pinecone_client(self) -> Pinecone:
        if not self._pc:
            if not self.pinecone_api_key:
                raise ValueError(ERROR_PINECONE_KEY_MISSING)
            self._pc = Pinecone(api_key=self.pinecone_api_key)
        return self._pc

    def get_groq_client(self) -> Groq:
        if not self._groq:
            if not self.groq_api_key:
                raise ValueError(ERROR_GROQ_KEY_MISSING)
            self._groq = Groq(api_key=self.groq_api_key)
        return self._groq

    def ensure_index(self):
        """Checks if index exists; if not, creates a serverless index with 1024 dims (for multilingual-e5-large)."""
        pc = self.get_pinecone_client()
        existing_indexes = [idx.name for idx in pc.list_indexes()]

        # multilingual-e5-large is 1024 dims
        dimension = 1024 if "e5-large" in self.embedding_model else 768

        if self.pinecone_index_name not in existing_indexes:
            pc.create_index(
                name=self.pinecone_index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=self.pinecone_cloud,
                    region=self.pinecone_region
                )
            )
            # Wait until ready
            while not pc.describe_index(self.pinecone_index_name).status['ready']:
                time.sleep(1)

        self._index = pc.Index(self.pinecone_index_name)
        return self._index

    def get_index(self):
        if not self._index:
            self.ensure_index()
        return self._index

    def generate_embeddings(self, texts: List[str], input_type: str = "passage") -> List[List[float]]:
        """Generates embeddings using Pinecone's serverless inference API."""
        pc = self.get_pinecone_client()
        embeddings_res = pc.inference.embed(
            model=self.embedding_model,
            inputs=texts,
            parameters={"input_type": input_type, "truncate": "END"}
        )
        return [item["values"] for item in embeddings_res]

    def delete_document_vectors(self, doc_name: str) -> Dict[str, Any]:
        """Deletes all vector chunks associated with a specific document from Pinecone."""
        try:
            index = self.get_index()
            # Delete by metadata filter (supported in Pinecone serverless)
            index.delete(filter={"doc_name": {"$eq": doc_name}})
            return {"status": "success", "message": f"Deleted vectors for {doc_name} from Pinecone"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def index_document(self, file_path: str, purge_existing: bool = True) -> Dict[str, Any]:
        """Parses DOCX file hierarchically and indexes chunks into Pinecone (replaces old vectors of this doc)."""
        doc_name = os.path.basename(file_path)
        
        # Purge existing vectors for this specific document first (incremental sync, no whole-db reindex)
        if purge_existing:
            try:
                self.delete_document_vectors(doc_name)
            except Exception:
                pass

        index = self.get_index()
        chunks = self.parser.create_chunks(file_path)
        if not chunks:
            return {"status": "warning", "message": "No content found in document", "chunks_indexed": 0}

        texts_to_embed = [c["text"] for c in chunks]
        embeddings = self.generate_embeddings(texts_to_embed, input_type="passage")

        records = []
        for chunk, emb in zip(chunks, embeddings):
            records.append({
                "id": chunk["chunk_id"],
                "values": emb,
                "metadata": {
                    "doc_name": chunk["doc_name"],
                    "breadcrumb": chunk["breadcrumb"],
                    "content_type": chunk["content_type"],
                    "text": chunk["text"],
                    "raw_content": chunk["raw_content"]
                }
            })

        # Upsert in batches of 50
        batch_size = 50
        for i in range(0, len(records), batch_size):
            index.upsert(vectors=records[i:i + batch_size])

        return {
            "status": "success",
            "document": doc_name,
            "chunks_indexed": len(records),
            "table_chunks": sum(1 for c in chunks if c["content_type"] == "table")
        }

    def retrieve_context(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieves top-k context chunks from Pinecone vector DB."""
        index = self.get_index()
        query_emb = self.generate_embeddings([query], input_type="query")[0]

        query_res = index.query(
            vector=query_emb,
            top_k=top_k,
            include_metadata=True
        )

        results = []
        for match in query_res.matches:
            meta = match.metadata or {}
            results.append({
                "chunk_id": match.id,
                "score": float(match.score),
                "breadcrumb": meta.get("breadcrumb", ""),
                "content_type": meta.get("content_type", "text"),
                "text": meta.get("text", ""),
                "raw_content": meta.get("raw_content", meta.get("text", "")),
                "doc_name": meta.get("doc_name", "")
            })

        return results

    def build_prompt(self, query: str, context_chunks: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Builds system prompt and context augmented conversation for Groq."""
        # Build context block
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

        # Include prior conversation history if present (last 4 turns)
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
