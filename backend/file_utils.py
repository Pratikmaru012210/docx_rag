import os
import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO

from backend.constants import ERROR_INVALID_FILENAME


def resolve_document_path(data_dir: str, filename: str) -> Path:
    """Resolve a document filename and prevent access outside the data directory."""
    if not filename or filename in {".", ".."} or any(
        separator in filename for separator in ("/", "\\")
    ) or "\x00" in filename:
        raise ValueError(ERROR_INVALID_FILENAME)

    root = Path(data_dir).resolve()
    document_path = (root / filename).resolve()
    if document_path.parent != root:
        raise ValueError(ERROR_INVALID_FILENAME)

    return document_path


def save_document_atomically(data_dir: str, filename: str, source: BinaryIO) -> Path:
    """Write a complete upload before making it visible, without replacing a document."""
    target_path = resolve_document_path(data_dir, filename)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=data_dir, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            shutil.copyfileobj(source, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())

        os.link(temporary_path, target_path)
        return target_path
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)