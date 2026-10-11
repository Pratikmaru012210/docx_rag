# FMCG SOP RAG Intelligence Chatbot

A high-precision RAG (Retrieval-Augmented Generation) system built for **FMCG Supply Chain & Standard Operating Procedure (SOP) documents**. Preserves complete context across **hierarchical headings, bullet procedures, and multi-column tables (e.g., RACI accountability matrices)** without data loss.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Vector DB**: ChromaDB HTTP server with Gemini embeddings (`gemini-embedding-001`)
- **LLM**: Groq API (`openai/gpt-oss-20b` by default; configurable with `GROQ_MODEL`)
- **Document Parser**: Sequential XML Traversal with `python-docx`
- **Frontend**: React + Vite + Vanilla CSS (Glassmorphism & dark theme) + `react-markdown` with `remark-gfm`

---

## 🚀 Getting Started

### Prerequisites

- Windows with PowerShell
- Python 3.12
- Node.js LTS and npm
- A Gemini API key for embeddings
- A Groq API key for chat responses

Run the following commands from the repository root (the folder containing `backend` and `frontend`).

### 1. Create and install the Python environment

Create a virtual environment once:

```powershell
py -3.12 -m venv backend\venv
```

Activate it and install backend dependencies:

```powershell
.\backend\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

If PowerShell blocks activation, allow scripts for this terminal session and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\backend\venv\Scripts\Activate.ps1
```

### 2. Configure backend credentials

Create your local environment file from the checked-in example:

```powershell
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` and set your credentials:

```env
# Chat model (get a key from https://console.groq.com/keys)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

# Embedding model (get a key from https://aistudio.google.com/apikey)
GEMINI_AI_API=your_gemini_api_key
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

# Local ChromaDB server and collection
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=fmcg-sop-rag

# Frontend origin allowed by the API
CORS_ORIGINS=http://localhost:5173
```

Keep `backend/.env` private. It is excluded from Git; do not put real keys in source files or commit them.

---

### 3. Start ChromaDB

Open a **new PowerShell terminal** at the repository root. Activate the environment, then start ChromaDB:

```powershell
.\backend\venv\Scripts\Activate.ps1
chroma run --path .\backend\chroma_db --port 8001
```

Leave this terminal running. Chroma's persistent local data is stored in `backend\chroma_db`, is ignored by Git, and is created automatically when the server starts.

You can verify the server from another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/v2/heartbeat
```

### 4. Start the FastAPI backend

Open a **second new PowerShell terminal** at the repository root:

```powershell
.\backend\venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --port 8000
```

---

### 5. Install and start the React frontend

Open a **third PowerShell terminal** at the repository root:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser. Keep the ChromaDB, FastAPI, and Vite terminals running while using the application.

### 6. Upload and verify a document

1. Upload a `.docx` file in the app. The frontend sends it to FastAPI, which stores the file under the project `data` directory and indexes its chunks in ChromaDB.
2. Confirm the upload status reports a nonzero number of indexed chunks. The document list also displays its chunk count.
3. Ask a question about the document. Matching chunks are retrieved from ChromaDB and the answer is streamed from Groq.

If the app reports **0 chunks**, use **Sync** to retry and check that the file is a readable `.docx`. If an upload or chat fails, inspect the FastAPI terminal for the detailed error and confirm the ChromaDB terminal is still running.

Local service URLs:

- ChromaDB: **http://127.0.0.1:8001** (heartbeat: `/api/v2/heartbeat`)
- FastAPI: **http://127.0.0.1:8000** (interactive API docs: `/docs`)
- Frontend: **http://localhost:5173**

---

## 📂 Project Structure

```
Word_POC/
├── backend/
│   ├── venv/              # Local Python virtual environment (not committed)
│   ├── chroma_db/         # Persistent ChromaDB data (not committed)
│   ├── .env               # Local API keys and settings (not committed)
│   ├── .env.example       # Environment variable template
│   ├── main.py            # FastAPI app configuration and router registration
│   ├── api/               # System, document, and RAG route modules
│   ├── services/          # Document, vector-store, and LLM orchestration
│   ├── config.py          # Environment-backed application settings
│   ├── constants.py       # Shared prompts, MIME types, and response text
│   ├── file_utils.py      # Safe paths and atomic document writes
│   ├── parser.py          # Hierarchical DOCX & Table Markdown Serializer
│   ├── rag_service.py     # ChromaDB vector indexing, search & Groq streaming
│   └── requirements.txt   # Python dependencies
├── data/                  # Uploaded DOCX files (created automatically; not committed)
├── frontend/              # Vite React Chat Interface
│   ├── src/
│   │   ├── App.jsx        # Application composition and layout
│   │   ├── components/    # Reusable layout and feature UI
│   │   ├── features/      # Chat, document, and reference workflows
│   │   ├── shared/        # Shared frontend utilities
│   │   ├── constants.js   # Shared UI suggestions and confirmation text
│   │   └── index.css      # Modern Glassmorphism CSS Design System
│   └── vite.config.js     # API reverse proxy to localhost:8000
└── README.md              # Setup and run instructions
```
