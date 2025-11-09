import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Gemini API Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_EMBEDDING_MODEL: str = "models/embedding-001"
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    
    # Database Configuration
    SQLITE_DB_PATH: str = "./storage/sqlite/sessions.db"
    CHROMA_DB_PATH: str = "./storage/chroma"
    CHROMA_COLLECTION_NAME: str = "assessments"
    
    # FastAPI Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    API_WORKERS: int = 1
    
    # Chainlit Configuration
    CHAINLIT_HOST: str = "0.0.0.0"
    CHAINLIT_PORT: int = 8001
    
    # Security
    REFRESH_API_KEY: str
    CORS_ORIGINS: str = "http://localhost:8001,http://localhost:3000"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Scraping Configuration
    SHL_CATALOG_URL: str = "https://www.shl.com/solutions/products/product-catalog/"
    SCRAPER_DELAY: float = 1.5
    SCRAPER_TIMEOUT: int = 30
    
    # RAG Configuration
    RAG_TOP_K: int = 15
    RAG_FINAL_SELECT_MIN: int = 5
    RAG_FINAL_SELECT_MAX: int = 10
    EMBEDDING_BATCH_SIZE: int = 10
    
    # Assessment Data
    ASSESSMENTS_JSON_PATH: str = "./data/shl_assessments.json"
    TRAIN_SET_PATH: str = "./data/labeled_train_set.json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            Path(self.SQLITE_DB_PATH).parent,
            Path(self.CHROMA_DB_PATH),
            Path(self.LOG_FILE).parent,
            Path(self.ASSESSMENTS_JSON_PATH).parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()