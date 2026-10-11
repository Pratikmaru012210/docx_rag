import sys
from pathlib import Path

# Add project root directory to sys.path so 'backend.*' imports resolve cleanly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_documents import router as documents_router
from backend.api.routes_rag import router as rag_router
from backend.api.routes_system import router as system_router
from backend.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/", tags=["System"])
def read_root():
    """Return a small health response confirming that the API process is running."""
    return {"status": "online", "message": "FMCG SOP RAG Backend is running", "docs_url": "/docs"}


app.include_router(system_router)
app.include_router(documents_router)
app.include_router(rag_router)
