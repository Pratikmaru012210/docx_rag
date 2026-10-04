import time
from typing import Any, Dict, List, Optional

from pinecone import Pinecone, ServerlessSpec

from backend.config import settings
from backend.constants import ERROR_PINECONE_KEY_MISSING


class VectorStoreService:
    """Manages Pinecone Serverless vector storage, indexing, and similarity retrieval."""

    def __init__(self):
        """Initialize empty client and index caches for lazy Pinecone setup."""
        self._pc: Optional[Pinecone] = None
        self._index = None

    def get_client(self) -> Pinecone:
        """Lazily construct the Pinecone client using the configured API key."""
        if not self._pc:
            if not settings.PINECONE_API_KEY:
                raise ValueError(ERROR_PINECONE_KEY_MISSING)
            self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        return self._pc

    def ensure_index(self):
        """Ensures the target Pinecone index exists with appropriate dimension and metric."""
        pc = self.get_client()
        existing_indexes = [idx.name for idx in pc.list_indexes()]

        if settings.PINECONE_INDEX_NAME not in existing_indexes:
            pc.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD,
                    region=settings.PINECONE_REGION
                )
            )
            deadline = time.monotonic() + settings.PINECONE_INDEX_READY_TIMEOUT_SECONDS
            # Poll against a monotonic deadline so system clock changes cannot affect the timeout.
            while not pc.describe_index(settings.PINECONE_INDEX_NAME).status['ready']:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Pinecone index '{settings.PINECONE_INDEX_NAME}' did not become ready "
                        f"within {settings.PINECONE_INDEX_READY_TIMEOUT_SECONDS} seconds."
                    )
                time.sleep(1)

        self._index = pc.Index(settings.PINECONE_INDEX_NAME)
        return self._index

    def get_index(self):
        """Return the cached index handle, creating or waiting for the index if needed."""
        if not self._index:
            self.ensure_index()
        return self._index

    def generate_embeddings(self, texts: List[str], input_type: str = "passage") -> List[List[float]]:
        """Generates dense embeddings via Pinecone Serverless Inference API."""
        pc = self.get_client()
        embeddings_res = pc.inference.embed(
            model=settings.EMBEDDING_MODEL,
            inputs=texts,
            parameters={"input_type": input_type, "truncate": "END"}
        )
        return [item["values"] for item in embeddings_res]

    def delete_document_vectors(self, doc_name: str) -> Dict[str, Any]:
        """Purges vectors associated with a specific document from Pinecone via metadata filter."""
        index = self.get_index()
        index.delete(filter={"doc_name": {"$eq": doc_name}})
        return {"status": "success", "message": f"Purged vectors for {doc_name}"}

    def upsert_chunks(self, doc_name: str, chunks: List[Dict[str, Any]]) -> int:
        """Embeds and upserts document chunks into Pinecone in batches."""
        if not chunks:
            return 0

        records = self._build_records(doc_name, chunks)
        self._upsert_records(records)
        return len(records)

    def replace_document_chunks(self, doc_name: str, chunks: List[Dict[str, Any]]) -> int:
        """Builds replacement vectors before purging existing vectors for the document."""
        records = self._build_records(doc_name, chunks) if chunks else []
        self.delete_document_vectors(doc_name)
        if records:
            self._upsert_records(records)
        return len(records)

    def _build_records(self, doc_name: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Embed each chunk and build Pinecone records with retrieval metadata."""
        texts_to_embed = [c["text"] for c in chunks]
        embeddings = self.generate_embeddings(texts_to_embed, input_type="passage")
        if len(embeddings) != len(chunks):
            raise RuntimeError("Embedding service returned a different number of vectors than requested.")
        if any(len(embedding) != settings.EMBEDDING_DIMENSION for embedding in embeddings):
            raise ValueError(
                f"Embedding dimension does not match the configured index dimension "
                f"({settings.EMBEDDING_DIMENSION})."
            )

        records = []
        for chunk, emb in zip(chunks, embeddings):
            records.append({
                "id": chunk["chunk_id"],
                "values": emb,
                "metadata": {
                    "doc_name": doc_name,
                    "breadcrumb": chunk["breadcrumb"],
                    "content_type": chunk["content_type"],
                    "text": chunk["text"],
                    "raw_content": chunk["raw_content"]
                }
            })
        return records

    def _upsert_records(self, records: List[Dict[str, Any]]) -> None:
        """Upsert records in bounded batches to keep each provider request manageable."""
        index = self.get_index()
        batch_size = 50
        for i in range(0, len(records), batch_size):
            index.upsert(vectors=records[i:i + batch_size])

    def similarity_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Performs cosine similarity search for a query string."""
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
