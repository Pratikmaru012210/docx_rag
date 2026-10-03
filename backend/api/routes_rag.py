import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.config import settings
from backend.file_utils import resolve_document_path
from backend.rag_service import RAGService
from backend.constants import ERROR_FILE_MISSING_FOR_INDEX, ERROR_INDEX

router = APIRouter(prefix="/api", tags=["RAG"])
rag_service = RAGService()


class IndexRequest(BaseModel):
    filename: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    top_k: int = Field(default=4, ge=1, le=10)


@router.post("/index")
def index_documents(request: IndexRequest):
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
            raise HTTPException(status_code=500, detail=ERROR_INDEX.format(error=exc)) from exc

    results = []
    for filename in os.listdir(settings.DATA_DIR):
        if filename.lower().endswith(".docx"):
            try:
                path = resolve_document_path(settings.DATA_DIR, filename)
                results.append(rag_service.index_document(str(path)))
            except Exception as exc:
                results.append({"document": filename, "status": "error", "error": str(exc)})
    return {"results": results}


@router.post("/search-debug")
def search_debug(query: str = Query(..., description="User search query"), top_k: int = Query(4, ge=1, le=10)):
    try:
        return {"query": query, "chunks": rag_service.retrieve_context(query, top_k=top_k)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat")
def chat_stream(request: ChatRequest):
    history = [{"role": message.role, "content": message.content} for message in request.history]

    def event_generator():
        try:
            for event in rag_service.stream_chat(request.query, chat_history=history, top_k=request.top_k):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )