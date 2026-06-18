"""
Configuration settings for AI Legal Simplifier
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
VECTOR_STORE_DIR.mkdir(exist_ok=True)

# File constraints
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
ALLOWED_EXTENSIONS = {".pdf"}

# Ollama settings
OLLAMA_MODEL = "qwen2.5:3b"  # 3B model fits in 4GB VRAM
OLLAMA_BASE_URL = "http://localhost:11434"

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Risk keywords for detection
RISK_KEYWORDS = {
    "HIGH": [
        "termination", "terminate", "breach", "default", "penalty", "penalties",
        "indemnify", "indemnification", "liable", "liability", "damages",
        "liquidated damages", "non-compete", "non-disclosure", "confidential",
        "proprietary", "trade secret", "injunctive relief", "specific performance"
    ],
    "MEDIUM": [
        "obligation", "duty", "responsibility", "compliance", "violation",
        "remedy", "cure", "notice", "written notice", "material breach",
        "intellectual property", "ownership", "assignment"
    ],
    "LOW": [
        "agreement", "contract", "party", "parties", "effective date",
        "term", "renewal", "amendment", "modification"
    ]
}

# Legal disclaimer
LEGAL_DISCLAIMER = """
⚠️ IMPORTANT DISCLAIMER:
This tool provides simplified explanations of legal text for educational purposes only.
This is NOT legal advice. Always consult with a qualified attorney for legal matters.
The AI may make errors - verify all information independently.
"""