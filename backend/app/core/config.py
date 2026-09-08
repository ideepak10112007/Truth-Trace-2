from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/


class Settings(BaseSettings):
    APP_NAME: str = "TRUTH TRACE"
    APP_VERSION: str = "1.0"
    ORG_NAME: str = "Chandigarh Police"
    ORG_UNIT: str = "Digital Forensics Unit"

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'truthtrace.db'}"
    STORAGE_DIR: Path = BASE_DIR / "app" / "storage"

    # CORS for the Vite dev server
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Similarity: max Hamming distance (out of 64 bits) counted as a "match"
    PHASH_MATCH_THRESHOLD: int = 12

    class Config:
        env_file = ".env"


settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
