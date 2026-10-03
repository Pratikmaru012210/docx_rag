from backend.services.vector_store import VectorStoreService
from backend.services.llm_service import LLMService
from backend.services.document_service import DocumentService

# Singleton instances for dependency injection
vector_store_service = VectorStoreService()
llm_service = LLMService()
document_service = DocumentService(vector_store=vector_store_service)

__all__ = [
    "VectorStoreService",
    "LLMService",
    "DocumentService",
    "vector_store_service",
    "llm_service",
    "document_service"
]
