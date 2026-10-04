# FMCG SOP RAG Intelligence Chatbot

A high-precision RAG (Retrieval-Augmented Generation) system built for **FMCG Supply Chain & Standard Operating Procedure (SOP) documents**. Preserves complete context across **hierarchical headings, bullet procedures, and multi-column tables (e.g., RACI accountability matrices)** without data loss.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Vector DB**: Pinecone Serverless Vector Database (`multilingual-e5-large` / `llama-text-embed-v2` embeddings)
- **LLM**: Groq API (`openai/gpt-oss-20b` by default; configurable with `GROQ_MODEL`)
- **Document Parser**: Sequential XML Traversal with `python-docx`
- **Frontend**: React + Vite + Vanilla CSS (Glassmorphism & dark theme) + `react-markdown` with `remark-gfm`

---

## 🚀 Getting Started

### 1. Configure Environment Credentials
Open `backend/.env` and add your keys:

```env
# 1. Groq API Key (Free from https://console.groq.com/keys)
GROQ_API_KEY=gsk_...

# 2. Pinecone API Key (Free from https://app.pinecone.io/)
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=fmcg-sop-rag
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Embedding model
EMBEDDING_MODEL=multilingual-e5-large

# Comma-separated browser origins allowed to call the API
CORS_ORIGINS=http://localhost:5173
```

---

### 2. Start the FastAPI Backend
Open a terminal in the project root:

```powershell
.\backend\venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --port 8000
```

---

### 3. Start the React Frontend
Open another terminal:

```powershell
cd frontend
npm run dev
```

Visit **http://localhost:5173** in your browser.

---

## 📂 Project Structure

```
Word_POC/
├── backend/
│   ├── venv/              # Local Python virtual environment (not committed)
│   ├── main.py            # FastAPI app configuration and router registration
│   ├── api/               # System, document, and RAG route modules
│   ├── services/          # Document, vector-store, and LLM orchestration
│   ├── config.py          # Environment-backed application settings
│   ├── constants.py       # Shared prompts, MIME types, and response text
│   ├── file_utils.py      # Safe paths and atomic document writes
│   ├── parser.py          # Hierarchical DOCX & Table Markdown Serializer
│   ├── rag_service.py     # Pinecone vector indexing, search & Groq streaming
│   └── requirements.txt   # Python dependencies
├── data/                  # Local document storage (created automatically)
├── frontend/              # Vite React Chat Interface
│   ├── src/
│   │   ├── App.jsx        # Application composition and layout
│   │   ├── components/    # Reusable layout and feature UI
│   │   ├── features/      # Chat, document, and reference workflows
│   │   ├── shared/        # Shared frontend utilities
│   │   ├── constants.js   # Shared UI suggestions and confirmation text
│   │   └── index.css      # Modern Glassmorphism CSS Design System
│   └── vite.config.js     # API reverse proxy to localhost:8000
└── backend/.env           # Local environment variables (API keys; do not commit)
```
