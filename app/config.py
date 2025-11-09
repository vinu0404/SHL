"""
Configuration settings - Updated for Railway deployment
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Gemini API Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_EMBEDDING_MODEL: str = "models/embedding-001"
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./storage/sqlite/sessions.db")
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./storage/chroma")
    CHROMA_COLLECTION_NAME: str = "assessments"

    # FastAPI Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("PORT", "8000"))  # Railway provides PORT env
    API_RELOAD: bool = False  # Disable reload in production
    API_WORKERS: int = 1

    # Chainlit Configuration
    CHAINLIT_HOST: str = "0.0.0.0"
    CHAINLIT_PORT: int = 8001

    # Security
    REFRESH_API_KEY: str = "shl-secure-refresh-key-2024"
    CORS_ORIGINS: str = "*"  # Update with your actual domain after deployment

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # Scraping Configuration
    SHL_CATALOG_URL: str = "https://www.shl.com/solutions/products/product-catalog/"
    SCRAPER_DELAY: int = 1
    SCRAPER_TIMEOUT: int = 30

    # RAG Configuration
    RAG_TOP_K: int = 10
    RAG_FINAL_SELECT_MIN: int = 5
    RAG_FINAL_SELECT_MAX: int = 7
    EMBEDDING_BATCH_SIZE: int = 10

    # Assessment Data
    ASSESSMENTS_JSON_PATH: str = "./data/shl_assessments.json"
    TRAIN_SET_PATH: str = "./data/labeled_train_set.json"
    
    # Railway specific
    RAILWAY_ENVIRONMENT: str = os.getenv("RAILWAY_ENVIRONMENT", "development")
    RAILWAY_STATIC_URL: str = os.getenv("RAILWAY_STATIC_URL", "")

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()