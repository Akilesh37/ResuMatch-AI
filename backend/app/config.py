import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
STATIC_DIR = BASE_DIR / "frontend"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = f"sqlite:///{STORAGE_DIR}/resume_system.db"

# Tesseract OCR path configuration
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "/opt/homebrew/bin/tesseract")
if not os.path.exists(TESSERACT_CMD):
    # Fallback to standard path
    TESSERACT_CMD = "tesseract"

# Embedding Model Configuration
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Scoring Weight Defaults
DEFAULT_WEIGHTS = {
    "semantic": 0.40,
    "skills": 0.35,
    "experience": 0.15,
    "keywords": 0.10
}
