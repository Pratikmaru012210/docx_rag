import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

from backend.services import document_service
from backend.schemas import DocumentListResponse
from backend.constants import DOCX_MIME_TYPE, ERROR_FILE_ALREADY_EXISTS

router = APIRouter(prefix="/api", tags=["Documents"])
logger = logging.getLogger(__name__)


@router.get("/documents", response_model=DocumentListResponse)
def list_documents():
    """Lists all SOP files with stats and Pinecone vectorization counts."""
    files = document_service.list_documents()
    return {"documents": files}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), auto_sync: bool = True):
    """Uploads a DOCX file to data repository and optionally triggers single-doc sync."""
    try:
        document_service.save_uploaded_file(file)
        result = {
            "filename": file.filename,
            "message": "File successfully uploaded.",
            "indexed": False
        }
        if auto_sync:
            sync_res = document_service.sync_document(file.filename)
            result["indexed"] = True
            result["index_details"] = sync_res
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=ERROR_FILE_ALREADY_EXISTS) from exc
    except Exception as exc:
        logger.exception("Document upload failed")
        raise HTTPException(status_code=500, detail="Document upload failed; check backend logs.") from exc


@router.delete("/documents/{filename}")
def delete_document(filename: str):
    """Deletes document file and purges associated vectors from Pinecone."""
    try:
        return document_service.delete_document(filename)
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Document deletion failed")
        raise HTTPException(status_code=500, detail="Document deletion failed; check backend logs.") from exc


@router.post("/documents/{filename}/reindex")
def reindex_single_document(filename: str):
    """Re-indexes only this single document in Pinecone."""
    try:
        res = document_service.sync_document(filename)
        return {
            "status": "success",
            "message": f"Successfully synced {filename} in Pinecone.",
            "details": res
        }
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Document re-index failed")
        raise HTTPException(status_code=500, detail="Document re-index failed; check backend logs.") from exc


@router.get("/documents/{filename}/preview")
def preview_document_structure(filename: str):
    """Returns parsed hierarchical chunks and tables for structure inspection."""
    try:
        return document_service.get_document_preview(filename)
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Document preview failed")
        raise HTTPException(status_code=500, detail="Document preview failed; check backend logs.") from exc


@router.get("/documents/{filename}/download-docx")
def download_original_docx(filename: str):
    """Downloads the raw original DOCX file."""
    try:
        fpath = document_service.get_document_path(filename)
        return FileResponse(path=fpath, filename=filename, media_type=DOCX_MIME_TYPE)
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/export-tables")
def export_tables(filename: str = Query(..., description="Document filename in data directory")):
    """Extracts all tables from the document and compiles them into a markdown file."""
    try:
        return document_service.export_document_tables(filename)
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as exc:
        logger.exception("Table export failed")
        raise HTTPException(status_code=500, detail="Table export failed; check backend logs.") from exc
