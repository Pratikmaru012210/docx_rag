import unittest
from unittest.mock import Mock, patch

import numpy as np

from backend.services.vector_store import VectorStoreService


class VectorStoreTests(unittest.TestCase):
    def test_generate_embeddings_normalizes_numpy_vectors(self):
        service = VectorStoreService()
        service._embedding_function = Mock(
            return_value=[np.array([0.5, 0.25], dtype=np.float32)]
        )

        embeddings = service.generate_embeddings(["procedure"])

        self.assertEqual(embeddings, [[0.5, 0.25]])

    def test_client_uses_configured_chroma_http_endpoint(self):
        service = VectorStoreService()
        with patch("backend.services.vector_store.chromadb.HttpClient") as http_client:
            service.get_client()
        http_client.assert_called_once_with(host="localhost", port=8001)

    def test_rejects_incomplete_embedding_response_before_replacing_vectors(self):
        service = VectorStoreService()
        service.generate_embeddings = Mock(return_value=[])
        service.delete_document_vectors = Mock()

        with self.assertRaisesRegex(RuntimeError, "different number of vectors"):
            service.replace_document_chunks(
                "procedure.docx",
                [{
                    "text": "procedure",
                    "chunk_id": "chunk-1",
                    "breadcrumb": "Section 1",
                    "content_type": "text",
                    "raw_content": "procedure",
                }],
            )

        service.delete_document_vectors.assert_not_called()

    def test_replacement_builds_embeddings_before_deleting_existing_vectors(self):
        service = VectorStoreService()
        service.generate_embeddings = Mock(side_effect=RuntimeError("embedding unavailable"))
        service.delete_document_vectors = Mock()

        with self.assertRaisesRegex(RuntimeError, "embedding unavailable"):
            service.replace_document_chunks(
                "procedure.docx",
                [{
                    "text": "procedure",
                    "chunk_id": "chunk-1",
                    "breadcrumb": "Section 1",
                    "content_type": "text",
                    "raw_content": "procedure",
                }],
            )

        service.delete_document_vectors.assert_not_called()

    def test_delete_document_vectors_propagates_provider_failures(self):
        service = VectorStoreService()
        collection = Mock()
        collection.delete.side_effect = RuntimeError("provider unavailable")
        service.get_collection = Mock(return_value=collection)

        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            service.delete_document_vectors("procedure.docx")

    def test_upsert_writes_embeddings_documents_and_retrieval_metadata(self):
        service = VectorStoreService()
        service.generate_embeddings = Mock(return_value=[[0.1, 0.2]])
        collection = Mock()
        service.get_collection = Mock(return_value=collection)
        chunks = [
            {
                "chunk_id": "procedure.docx_chunk_0000",
                "text": "Procedure content",
                "breadcrumb": "Section 1",
                "content_type": "text",
                "raw_content": "Procedure",
            }
        ]

        count = service.upsert_chunks("procedure.docx", chunks)

        self.assertEqual(count, 1)
        collection.upsert.assert_called_once_with(
            ids=["procedure.docx_chunk_0000"],
            embeddings=[[0.1, 0.2]],
            documents=["Procedure content"],
            metadatas=[
                {
                    "doc_name": "procedure.docx",
                    "breadcrumb": "Section 1",
                    "content_type": "text",
                    "raw_content": "Procedure",
                }
            ],
        )

    def test_similarity_search_converts_cosine_distance_to_score(self):
        service = VectorStoreService()
        service.generate_embeddings = Mock(return_value=[[0.1, 0.2]])
        collection = Mock()
        collection.query.return_value = {
            "ids": [["procedure.docx_chunk_0000"]],
            "documents": [["Procedure content"]],
            "distances": [[0.25]],
            "metadatas": [[
                {
                    "doc_name": "procedure.docx",
                    "breadcrumb": "Section 1",
                    "content_type": "text",
                    "raw_content": "Procedure",
                }
            ]],
        }
        service.get_collection = Mock(return_value=collection)

        results = service.similarity_search("How to proceed?")

        self.assertEqual(
            results,
            [
                {
                    "chunk_id": "procedure.docx_chunk_0000",
                    "score": 0.75,
                    "breadcrumb": "Section 1",
                    "content_type": "text",
                    "text": "Procedure content",
                    "raw_content": "Procedure",
                    "doc_name": "procedure.docx",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
