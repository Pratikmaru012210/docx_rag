import json
import logging
import os
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.config import settings
from backend.file_utils import resolve_document_path
from backend.rag_service import RAGService
from backend.services import vector_store_service
from backend.constants import ERROR_FILE_MISSING_FOR_INDEX

router = APIRouter(prefix="/api", tags=["RAG"])
logger = logging.getLogger(__name__)
rag_service = RAGService(vector_store=vector_store_service)


class IndexRequest(BaseModel):
    filename: Optional[str] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    top_k: int = Field(default=4, ge=1, le=10)


@router.post("/index")
def index_documents(request: IndexRequest):
    """Index one requested document or process every DOCX in the data directory."""
    if request.filename:
        try:
            path = resolve_document_path(settings.DATA_DIR, request.filename)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not path.is_file():
            raise HTTPException(
                status_code=404,
                detail=ERROR_FILE_MISSING_FOR_INDEX.format(filename=request.filename),
            )
        try:
            return {"results": [rag_service.index_document(str(path))]}
        except Exception as exc:
            logger.exception("Document indexing failed for %s", request.filename)
            raise HTTPException(
                status_code=500,
                detail="Document indexing failed; check backend logs.",
            ) from exc

    # Continue through the directory even if one file fails, reporting each outcome.
    results = []
    for filename in os.listdir(settings.DATA_DIR):
        if filename.lower().endswith(".docx"):
            try:
                path = resolve_document_path(settings.DATA_DIR, filename)
                results.append(rag_service.index_document(str(path)))
            except Exception:
                logger.exception("Document indexing failed for %s", filename)
                results.append({
                    "document": filename,
                    "status": "error",
                    "error": "Document indexing failed; check backend logs.",
                })
    return {"results": results}


@router.post("/search-debug")
def search_debug(query: str = Query(..., description="User search query"), top_k: int = Query(4, ge=1, le=10)):
    """Return retrieved chunks for debugging the vector search without generating a reply."""
    try:
        return {"query": query, "chunks": rag_service.retrieve_context(query, top_k=top_k)}
    except Exception as exc:
        logger.exception("Vector search failed")
        raise HTTPException(status_code=500, detail="Vector search failed; check backend logs.") from exc


@router.post("/chat")
def chat_stream(request: ChatRequest):
    """Stream the generated answer and citation events to the client using SSE."""
    history = [{"role": message.role, "content": message.content} for message in request.history]

    def event_generator():
        """Convert each RAG event to an SSE data frame and report stream failures."""
        try:
            for event in rag_service.stream_chat(request.query, chat_history=history, top_k=request.top_k):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            logger.exception("Chat response generation failed")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Response generation failed; check backend logs.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )