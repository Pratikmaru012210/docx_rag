from io import BytesIO
import tempfile
import unittest
from pathlib import Path

from backend.file_utils import resolve_document_path, save_document_atomically


class ResolveDocumentPathTests(unittest.TestCase):
    def test_resolves_filename_inside_data_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assertEqual(resolve_document_path(directory, "procedure.docx"), root / "procedure.docx")

    def test_rejects_path_components_and_empty_names(self):
        with tempfile.TemporaryDirectory() as directory:
            for filename in ("../outside.docx", "folder/procedure.docx", "folder\\procedure.docx", "..", ""):
                with self.subTest(filename=filename):
                    with self.assertRaises(ValueError):
                        resolve_document_path(directory, filename)

    def test_rejects_symlink_that_escapes_data_directory(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            data_root = Path(directory)
            link = data_root / "outside.docx"
            try:
                link.symlink_to(Path(outside) / "secret.docx")
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation is not available in this environment")

            with self.assertRaises(ValueError):
                resolve_document_path(directory, "outside.docx")

    def test_saves_upload_atomically_without_replacing_existing_document(self):
        with tempfile.TemporaryDirectory() as directory:
            target = save_document_atomically(directory, "procedure.docx", BytesIO(b"complete"))
            self.assertEqual(target.read_bytes(), b"complete")

            with self.assertRaises(FileExistsError):
                save_document_atomically(directory, "procedure.docx", BytesIO(b"replacement"))

            self.assertEqual(target.read_bytes(), b"complete")
            self.assertEqual([path.name for path in Path(directory).iterdir()], ["procedure.docx"])


if __name__ == "__main__":
    unittest.main()