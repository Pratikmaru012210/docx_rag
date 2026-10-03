from fastapi import APIRouter
from backend.config import settings
from backend.schemas import SystemStatusResponse

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status():
    """Returns connectivity and configuration status for Pinecone and Groq."""
    return {
        "pinecone_configured": bool(settings.PINECONE_API_KEY),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "index_name": settings.PINECONE_INDEX_NAME,
        "groq_model": settings.GROQ_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL
    }
