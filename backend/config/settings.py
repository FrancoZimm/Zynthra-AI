"""Application settings and configuration.

Centralized configuration management using environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# === Database Configuration ===
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'tutor_ia_verificable')

# === Ollama Configuration ===
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')
DEFAULT_LLM_MODEL = os.environ.get('DEFAULT_LLM_MODEL', 'llama3.2:1b')
DEFAULT_EMBEDDING_MODEL = os.environ.get('DEFAULT_EMBEDDING_MODEL', 'nomic-embed-text')
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '300'))

# === RAG Configuration ===
CHUNK_SIZE_CHARS = int(os.environ.get('CHUNK_SIZE_CHARS', '1100'))
CHUNK_OVERLAP_CHARS = int(os.environ.get('CHUNK_OVERLAP_CHARS', '150'))
TOP_K_RESULTS = int(os.environ.get('TOP_K_RESULTS', '5'))

# === Confidence Thresholds ===
LOCAL_CONFIDENCE_THRESHOLD = float(os.environ.get('LOCAL_CONFIDENCE_THRESHOLD', '0.60'))
STRONG_LOCAL_CONFIDENCE_THRESHOLD = float(os.environ.get('STRONG_LOCAL_CONFIDENCE_THRESHOLD', '0.70'))
MIN_EVIDENCE_FOR_FULL_RESPONSE = float(os.environ.get('MIN_EVIDENCE_FOR_FULL_RESPONSE', '0.65'))

# === Anti-Copy Configuration ===
ENABLE_ANTI_COPY = os.environ.get('ENABLE_ANTI_COPY', 'true').lower() == 'true'
GUIDED_MODE_THRESHOLD = float(os.environ.get('GUIDED_MODE_THRESHOLD', '0.7'))

# === Document Storage ===
DOCS_DIR = ROOT_DIR / 'documents'
INDEX_DIR = ROOT_DIR / 'index'

# Ensure directories exist
DOCS_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

# === CORS Configuration ===
CORS_ORIGINS = os.environ.get(
    'CORS_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001'
).split(',')
