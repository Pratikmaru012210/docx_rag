from backend.services.document_service import DocumentService
from backend.services.llm_service import LLMService
from backend.services.vector_store import VectorStoreService

# Singleton instances for dependency injection
vector_store_service = VectorStoreService()
llm_service = LLMService()
document_service = DocumentService(vector_store=vector_store_service)

__all__ = [
    "DocumentService",
    "LLMService",
    "VectorStoreService",
    "document_service",
    "llm_service",
    "vector_store_service"
]
