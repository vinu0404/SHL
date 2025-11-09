from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ExtractJDRequest
from app.services.jd_fetcher_service import get_jd_fetcher_service
from app.database.sqlite_db import get_db
from app.utils.logger import get_logger
from app.utils.validators import validate_url

logger = get_logger("extract_jd_route")

router = APIRouter(tags=["utilities"])


@router.post("/extract-jd")
async def extract_job_description(
    request: ExtractJDRequest,
    db: Session = Depends(get_db)
):
    """
    Extract job description from URL
    
    Utility endpoint to fetch and extract job description text from a given URL.
    
    Args:
        request: Extract JD request with URL
        db: Database session
        
    Returns:
        Extracted JD text and metadata
    """
    jd_fetcher = get_jd_fetcher_service()
    
    logger.info(f"Extracting JD from URL: {request.url}")
    
    # Validate URL
    if not validate_url(request.url):
        logger.warning(f"Invalid URL: {request.url}")
        raise HTTPException(
            status_code=400,
            detail="Invalid URL format"
        )
    
    try:
        # Fetch JD
        result = await jd_fetcher.fetch_jd_from_url(request.url)
        
        if not result['success']:
            logger.warning(f"JD extraction failed: {result['error_message']}")
            raise HTTPException(
                status_code=400,
                detail=result['error_message']
            )
        
        jd_text = result['jd_text']
        metadata = result['metadata']
        
        logger.info(f"Successfully extracted JD ({len(jd_text)} characters)")
        
        return {
            "success": True,
            "url": request.url,
            "jd_text": jd_text,
            "text_length": len(jd_text),
            "metadata": metadata,
            "message": "Job description extracted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JD extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract job description: {str(e)}"
        )