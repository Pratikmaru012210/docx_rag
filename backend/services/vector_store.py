from typing import Any, Dict, List, Optional

import chromadb
from chromadb import EmbeddingFunction, Embeddings
from google import genai
from google.genai import types

from backend.config import settings
from backend.constants import ERROR_GEMINI_KEY_MISSING


class GeminiEmbeddingFunction(EmbeddingFunction):
    """Generate Chroma embeddings with Google's Gemini embedding API."""

    def __init__(self, api_key: str, task_type: str = "SEMANTIC_SIMILARITY"):
        self._client = genai.Client(api_key=api_key)
        self._task_type = task_type

    def __call__(self, input: List[str]) -> Embeddings:
        response = self._client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=input,
            config=types.EmbedContentConfig(task_type=self._task_type),
        )
        vectors = [embedding.values for embedding in response.embeddings]
        if any(vector is None for vector in vectors):
            raise RuntimeError("Gemini returned an embedding without vector values.")
        return [[float(value) for value in vector] for vector in vectors]


class VectorStoreService:
    """Manages ChromaDB collection storage, indexing, and similarity retrieval."""

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None
        self._embedding_function: Optional[GeminiEmbeddingFunction] = None

    def get_client(self) -> chromadb.ClientAPI:
        """Connect to the configured ChromaDB HTTP server on first use."""
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
        return self._client

    def get_embedding_function(self) -> GeminiEmbeddingFunction:
        """Create the Gemini embedding client lazily after validating its API key."""
        if self._embedding_function is None:
            if not settings.GEMINI_AI_API:
                raise ValueError(ERROR_GEMINI_KEY_MISSING)
            self._embedding_function = GeminiEmbeddingFunction(
                api_key=settings.GEMINI_AI_API
            )
        return self._embedding_function

    def get_collection(self):
        """Return the configured collection, creating it when it does not exist."""
        if self._collection is None:
            self._collection = self.get_client().get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                embedding_function=self.get_embedding_function(),
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate document or query embeddings using the demo's similarity task."""
        embedding_function = self.get_embedding_function()
        batch_size = 50
        embeddings = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            vectors = embedding_function(batch)
            if len(vectors) != len(batch):
                raise RuntimeError(
                    "Embedding service returned a different number of vectors than requested."
                )
            for vector in vectors:
                if vector is None or len(vector) == 0:
                    raise RuntimeError("Embedding service returned an empty vector.")
                embeddings.append([float(value) for value in vector])
        if len(embeddings) != len(texts):
            raise RuntimeError(
                "Embedding service returned a different number of vectors than requested."
            )
        return embeddings

    def delete_document_vectors(self, doc_name: str) -> Dict[str, Any]:
        """Delete all chunks belonging to a document from the Chroma collection."""
        self.get_collection().delete(where={"doc_name": doc_name})
        return {"status": "success", "message": f"Purged vectors for {doc_name}"}

    def upsert_chunks(self, doc_name: str, chunks: List[Dict[str, Any]]) -> int:
        """Embed and upsert document chunks into ChromaDB in bounded batches."""
        if not chunks:
            return 0

        records = self._build_records(doc_name, chunks)
        self._upsert_records(records)
        return len(records)

    def replace_document_chunks(
        self, doc_name: str, chunks: List[Dict[str, Any]]
    ) -> int:
        """Prepare replacement embeddings before deleting existing document chunks."""
        records = self._build_records(doc_name, chunks) if chunks else []
        self.delete_document_vectors(doc_name)
        if records:
            self._upsert_records(records)
        return len(records)

    def _build_records(
        self, doc_name: str, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        if len(embeddings) != len(chunks):
            raise RuntimeError(
                "Embedding service returned a different number of vectors than requested."
            )

        return [
            {
                "id": chunk["chunk_id"],
                "embedding": embedding,
                "text": chunk["text"],
                "metadata": {
                    "doc_name": doc_name,
                    "breadcrumb": chunk["breadcrumb"],
                    "content_type": chunk["content_type"],
                    "raw_content": chunk["raw_content"],
                },
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

    def _upsert_records(self, records: List[Dict[str, Any]]) -> None:
        """Upsert records in bounded batches to keep each request manageable."""
        collection = self.get_collection()
        batch_size = 50
        for start in range(0, len(records), batch_size):
            batch = records[start : start + batch_size]
            collection.upsert(
                ids=[record["id"] for record in batch],
                embeddings=[record["embedding"] for record in batch],
                documents=[record["text"] for record in batch],
                metadatas=[record["metadata"] for record in batch],
            )

    def similarity_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Search by cosine similarity and return the existing retrieval shape."""
        embedding = self.generate_embeddings([query])[0]
        results = self.get_collection().query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"],
        )

        matches = []
        ids = results["ids"][0]
        documents = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        for chunk_id, text, distance, metadata in zip(
            ids, documents, distances, metadatas
        ):
            metadata = metadata or {}
            matches.append(
                {
                    "chunk_id": chunk_id,
                    "score": float(1 - distance),
                    "breadcrumb": metadata.get("breadcrumb", ""),
                    "content_type": metadata.get("content_type", "text"),
                    "text": text or "",
                    "raw_content": metadata.get("raw_content", text or ""),
                    "doc_name": metadata.get("doc_name", ""),
                }
            )
        return matches
