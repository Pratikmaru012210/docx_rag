import time
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec

from backend.config import settings
from backend.constants import ERROR_PINECONE_KEY_MISSING


class VectorStoreService:
    """Manages Pinecone Serverless vector storage, indexing, and similarity retrieval."""

    def __init__(self):
        self._pc: Optional[Pinecone] = None
        self._index = None

    def get_client(self) -> Pinecone:
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
            while not pc.describe_index(settings.PINECONE_INDEX_NAME).status['ready']:
                time.sleep(1)

        self._index = pc.Index(settings.PINECONE_INDEX_NAME)
        return self._index

    def get_index(self):
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
        try:
            index = self.get_index()
            index.delete(filter={"doc_name": {"$eq": doc_name}})
            return {"status": "success", "message": f"Purged vectors for {doc_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def upsert_chunks(self, doc_name: str, chunks: List[Dict[str, Any]]) -> int:
        """Embeds and upserts chunks into Pinecone in batches."""
        if not chunks:
            return 0

        index = self.get_index()
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

        batch_size = 50
        for i in range(0, len(records), batch_size):
            index.upsert(vectors=records[i:i + batch_size])

        return len(records)

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
