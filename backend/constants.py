# Backend Static Constants, Prompts, and Error Messages

SYSTEM_INSTRUCTION_SOP = """You are an expert FMCG Supply Chain & Operations AI Assistant.
Your task is to provide accurate, comprehensive, and clear answers based strictly on the provided SOP documentation.

Guidelines:
1. Whenever answering, refer to the relevant Section Hierarchy and Tables provided in the context.
2. If the context contains tabular data (such as RACI matrix, timelines, stages, roles), represent or quote them cleanly using Markdown tables.
3. If information is missing from the provided context, state honestly that the SOP does not specify it rather than guessing.
4. Cite the specific SOP section or document path at the end of key points.
"""

DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

ERROR_DOCX_ONLY = "Only .docx files are supported."
ERROR_FILE_NOT_FOUND = "Specified file was not found in data repository."
ERROR_NO_TABLES = "No tables found in this document to export."
ERROR_PINECONE_KEY_MISSING = "PINECONE_API_KEY is not configured in .env."
ERROR_GROQ_KEY_MISSING = "GROQ_API_KEY is not configured in .env."

ERROR_INVALID_FILENAME = "Invalid document filename."
ERROR_FILE_ALREADY_EXISTS = "A document with this filename already exists."
ERROR_FILE_NOT_FOUND_IN_DATA = "File not found in data directory."
ERROR_FILE_MISSING_FOR_INDEX = "File {filename} not found in data directory."
ERROR_DELETE_FILE = "Failed to delete local file: {error}"
ERROR_REINDEX = "Re-indexing failed: {error}"
ERROR_INDEX = "Indexing failed: {error}"
