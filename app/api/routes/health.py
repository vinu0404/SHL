from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.schemas import HealthResponse
from app.database.sqlite_db import get_db
from app.database.chroma_db import get_chroma_client
from app.services.llm_service import get_llm_service
from app.utils.logger import get_logger

logger = get_logger("health_route")

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    
    Returns:
        Health status
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
        # Check ChromaDB
        chroma = get_chroma_client()
        doc_count = chroma.count_documents()
        
        # Check LLM service
        llm = get_llm_service()
        
        logger.info(f"Health check passed - ChromaDB docs: {doc_count}")
        
        return HealthResponse(status="healthy")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(status=f"unhealthy: {str(e)}")