"""
Application configuration, loaded from environment variables.
Copy .env.example to .env and fill in real values before running.
"""
import os
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings:
    PROJECT_NAME: str = "CivicFlow"
    PROBLEM_STATEMENT_ID: str = "SIH26034"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://civicflow:civicflow@localhost:5432/civicflow"
    )

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "reports")

    # "tesseract" | "demo" -- automatically falls back to "demo" if pytesseract / the
    # tesseract binary isn't available at runtime. See services/ocr_service.py.
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "tesseract")

    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]

    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
