import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from backend.services.document_service import DocumentService


class DocumentServiceTests(unittest.TestCase):
    def test_keeps_existing_vectors_when_document_parsing_fails(self):
        vector_store = Mock()
        service = DocumentService.__new__(DocumentService)
        service.vector_store = vector_store
        service.parser = Mock()
        service.parser.create_chunks.side_effect = RuntimeError("invalid document")
        service.get_document_path = Mock(return_value="procedure.docx")

        with self.assertRaisesRegex(RuntimeError, "invalid document"):
            service.sync_document("procedure.docx")

        vector_store.replace_document_chunks.assert_not_called()

    def test_keeps_local_document_when_vector_purge_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            document_path = Path(directory) / "procedure.docx"
            document_path.write_bytes(b"document")

            vector_store = Mock()
            vector_store.delete_document_vectors.side_effect = RuntimeError("provider unavailable")
            service = DocumentService.__new__(DocumentService)
            service.vector_store = vector_store
            service.get_document_path = Mock(return_value=str(document_path))

            with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
                service.delete_document("procedure.docx")

            self.assertTrue(document_path.exists())
            vector_store.delete_document_vectors.assert_called_once_with("procedure.docx")


if __name__ == "__main__":
    unittest.main()
