import unittest
from unittest.mock import Mock, patch

from backend.config import settings
from backend.services.vector_store import VectorStoreService


class VectorStoreTests(unittest.TestCase):
    def test_index_readiness_wait_has_a_timeout(self):
        service = VectorStoreService()
        client = Mock()
        client.list_indexes.return_value = []
        client.describe_index.return_value.status = {"ready": False}
        service.get_client = Mock(return_value=client)

        with patch.object(settings, "PINECONE_INDEX_READY_TIMEOUT_SECONDS", 0):
            with self.assertRaisesRegex(TimeoutError, "did not become ready"):
                service.ensure_index()

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
        index = Mock()
        index.delete.side_effect = RuntimeError("provider unavailable")
        service.get_index = Mock(return_value=index)

        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            service.delete_document_vectors("procedure.docx")


if __name__ == "__main__":
    unittest.main()
