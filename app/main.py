import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db, init_chroma, close_chroma
from app.services.vector_store_service import get_vector_store_service
from app.services.scraper_service import get_scraper_service
from app.api.middleware import LoggingMiddleware, RateLimitMiddleware
from app.api.routes import (
    health,
    recommend,
    chat,
    session,
    assessments,
    extract_jd,
    test_types,
    refresh
)
from app.utils.logger import get_logger

logger = get_logger("main")


async def initialize_vector_store():
    """Initialize vector store with assessments data"""
    try:
        vector_store = get_vector_store_service()
        
        # Check if already initialized
        count = vector_store.chroma_manager.count_documents()
        
        if count > 0:
            logger.info(f"Vector store already initialized with {count} documents")
            return
        
        logger.info("Vector store is empty, initializing with data...")
        
        # Load assessments from JSON
        scraper = get_scraper_service()
        assessments_path = Path(settings.ASSESSMENTS_JSON_PATH)
        
        if not assessments_path.exists():
            logger.warning(f"Assessments file not found at {assessments_path}")
            logger.info("Please run the scraper first to populate the data")
            return
        
        # Load and index assessments
        with open(assessments_path, 'r', encoding='utf-8') as f:
            assessments = json.load(f)
        
        logger.info(f"Loading {len(assessments)} assessments from JSON")
        
        indexed_count = await vector_store.index_assessments(assessments)
        
        logger.info(f"Successfully indexed {indexed_count} assessments")
        
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting SHL Assessment Recommendation System...")
    
    try:
        # Initialize databases
        logger.info("Initializing databases...")
        init_db()
        init_chroma()
        
        # Initialize vector store with data
        await initialize_vector_store()
        
        # Start auto-refresh task
        logger.info("Starting auto-refresh task...")
        await refresh.start_auto_refresh()
        
        logger.info("Startup complete!")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    try:
        # Stop auto-refresh
        await refresh.stop_auto_refresh()
        
        # Close databases
        await close_chroma()
        await close_db()
        
        logger.info("Shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation System",
    description="API for recommending SHL assessments based on job descriptions and queries",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(recommend.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(assessments.router, prefix="/api")
app.include_router(extract_jd.router, prefix="/api")
app.include_router(test_types.router, prefix="/api")
app.include_router(refresh.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SHL Assessment Recommendation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "SHL Assessment Recommendation System",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "recommend": "/api/recommend",
            "chat": "/api/chat",
            "session": "/api/session/{session_id}",
            "search": "/api/assessments/search",
            "test_types": "/api/test-types",
            "extract_jd": "/api/extract-jd",
            "refresh": "/api/refresh"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS
    )