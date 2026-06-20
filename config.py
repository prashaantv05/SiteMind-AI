import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# --- API Keys ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

# --- Model Configurations ---
# Google's recommended embedding model for converting text to vectors
EMBEDDING_MODEL_NAME = "gemini-embedding-001"

# The LLM used for reading the context and answering the question
LLM_MODEL_NAME = "gemini-2.5-flash"

# Temperature controls creativity. 0.0 means strictly factual.
LLM_TEMPERATURE = 0.0

# --- File Paths ---
FAISS_CACHE_PATH = "faiss_cache"
URLS_FILE_PATH = "urls.txt"

# --- Text Splitting Configurations ---
# The maximum number of characters per text chunk
CHUNK_SIZE = 1000
# How many characters should overlap between chunks to maintain sentence context
CHUNK_OVERLAP = 200

# --- Retrieval Settings ---
# How many matching chunks to retrieve from the database for the LLM to read
TOP_K_RESULTS = 3
