from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User search or conversational query")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Prior conversation history")
    top_k: Optional[int] = Field(default=4, ge=1, le=10, description="Number of vector chunks to retrieve")


class SourceCitation(BaseModel):
    chunk_id: str
    breadcrumb: str
    content_type: str
    score: float
    text: str
    raw_content: Optional[str] = None
    preview: Optional[str] = None


class DocumentInfo(BaseModel):
    filename: str
    size_kb: float
    modified: float
    chunks_count: int
    tables_count: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]


class IndexResponse(BaseModel):
    status: str
    document: str
    chunks_indexed: int
    table_chunks: int


class SystemStatusResponse(BaseModel):
    pinecone_configured: bool
    groq_configured: bool
    index_name: str
    groq_model: str
    embedding_model: str
