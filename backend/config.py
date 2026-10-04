import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FMCG SOP RAG Assistant API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Production-grade Context-preserving RAG API for FMCG & Industrial SOP Operations"
    CORS_ORIGINS: str = "http://localhost:5173"

    # API Keys & Cloud Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "fmcg-sop-rag"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    PINECONE_INDEX_READY_TIMEOUT_SECONDS: int = Field(default=120, ge=1)
    
    EMBEDDING_MODEL: str = "multilingual-e5-large"
    EMBEDDING_DIMENSION: int = 1024

    # Parsing & Chunking Defaults
    MAX_CHUNK_WORDS: int = 350
    CHUNK_OVERLAP_WORDS: int = 50

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        extra = "ignore"

    @property
    def allowed_origins(self) -> list[str]:
        """Parse the configured comma-separated browser origins into a clean list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)
