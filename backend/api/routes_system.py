from fastapi import APIRouter
from backend.config import settings
from backend.schemas import SystemStatusResponse

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status():
    """Returns configuration status for Gemini embeddings and Groq."""
    return {
        "gemini_configured": bool(settings.GEMINI_AI_API),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "collection_name": settings.CHROMA_COLLECTION_NAME,
        "groq_model": settings.GROQ_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
    }
