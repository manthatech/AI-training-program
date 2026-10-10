"""
config.py - All the settings for the app, in one place.

Each setting is read from an environment variable (or from the .env file).
If the variable is not set, we use the default value written after the comma.

Example:  LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
          -> use the LLM_MODEL from .env, or "gpt-4o-mini" if it isn't there.
"""
import os

from dotenv import load_dotenv

# Read the .env file (if there is one) into environment variables.
load_dotenv()

# ---------------------------------------------------------------- App
APP_NAME = "RAG Chatbot API"
API_KEY = os.getenv("API_KEY")            # if set, clients must send header "X-API-Key"
DATA_DIR = os.getenv("DATA_DIR", "data")  # the database and vector index are saved here

# ---------------------------------------------------------------- LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")   # openai | anthropic | groq | ollama
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# ---------------------------------------------------------------- Embeddings and reranker
# These models run on your own computer (free). They download on first start.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() == "true"
RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# ---------------------------------------------------------------- RAG (documents)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))         # characters per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))    # characters shared by neighbouring chunks
SEARCH_CANDIDATES = int(os.getenv("SEARCH_CANDIDATES", "20"))  # chunks fetched from the vector DB
SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "4"))             # chunks kept after reranking
MAX_UPLOAD_MB = 25

# ---------------------------------------------------------------- Memory
MEMORY_WINDOW_TURNS = int(os.getenv("MEMORY_WINDOW_TURNS", "6"))  # last N turns sent word-for-word
MEMORY_RECALL_K = int(os.getenv("MEMORY_RECALL_K", "3"))          # older turns recalled by similarity
EXTRACT_PROFILE = os.getenv("EXTRACT_PROFILE", "true").lower() == "true"

# ---------------------------------------------------------------- Tools
MAX_TOOL_ROUNDS = 5   # stop if the model keeps calling tools more than this
