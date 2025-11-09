import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.models.schemas import RefreshResponse
from app.models.database_models import VectorStoreMetadata
from app.services.scraper_service import get_scraper_service
from app.services.vector_store_service import get_vector_store_service
from app.database.sqlite_db import get_db
from app.api.dependencies import verify_refresh_api_key
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("refresh_route")

router = APIRouter(tags=["admin"])

# Global state for tracking refresh
_last_refresh_time = None
_refresh_in_progress = False
_auto_refresh_task = None


async def perform_refresh(db: Session) -> dict:
    """
    Perform the actual refresh operation
    
    Args:
        db: Database session
        
    Returns:
        Result dictionary
    """
    global _last_refresh_time, _refresh_in_progress
    
    if _refresh_in_progress:
        logger.warning("Refresh already in progress")
        return {
            "status": "skipped",
            "message": "Refresh already in progress",
            "assessments_count": 0
        }
    
    _refresh_in_progress = True
    
    try:
        logger.info("Starting assessment catalog refresh")
        
        scraper = get_scraper_service()
        vector_store = get_vector_store_service()
        
        # Step 1: Scrape latest assessments
        logger.info("Scraping SHL catalog...")
        assessments = await scraper.scrape_all_tests()
        
        if not assessments:
            logger.error("Scraping returned no assessments")
            raise Exception("Failed to scrape assessments")
        
        logger.info(f"Scraped {len(assessments)} assessments")
        
        # Step 2: Save to JSON file
        logger.info("Saving assessments to JSON...")
        scraper.save_to_json(assessments)
        
        # Step 3: Clear existing vector store
        logger.info("Clearing existing vector store...")
        await vector_store.clear_collection()
        
        # Step 4: Index new assessments
        logger.info("Indexing new assessments...")
        indexed_count = await vector_store.index_assessments(assessments)
        
        logger.info(f"Indexed {indexed_count} assessments")
        
        # Step 5: Update metadata in database
        try:
            metadata = VectorStoreMetadata(
                collection_name=settings.CHROMA_COLLECTION_NAME,
                document_count=indexed_count,
                update_source='api_refresh',
                update_notes=f'Automatic refresh completed successfully'
            )
            db.add(metadata)
            db.commit()
            logger.info("Updated vector store metadata")
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            db.rollback()
        
        _last_refresh_time = datetime.utcnow()
        
        logger.info("Refresh completed successfully")
        
        return {
            "status": "success",
            "message": "Assessment catalog refreshed successfully",
            "assessments_count": indexed_count,
            "timestamp": _last_refresh_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        return {
            "status": "error",
            "message": f"Refresh failed: {str(e)}",
            "assessments_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        _refresh_in_progress = False


async def auto_refresh_worker():
    """
    Background worker that automatically refreshes every 7 days
    """
    global _last_refresh_time
    
    logger.info("Auto-refresh worker started")
    
    # Get database session
    from app.database.sqlite_db import db_manager
    
    while True:
        try:
            # Wait for 7 days
            await asyncio.sleep(7 * 24 * 60 * 60)  # 7 days in seconds
            
            logger.info("Auto-refresh triggered (7 days elapsed)")
            
            # Perform refresh
            with db_manager.get_session() as db:
                result = await perform_refresh(db)
                logger.info(f"Auto-refresh result: {result['status']}")
            
        except Exception as e:
            logger.error(f"Auto-refresh worker error: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(60 * 60)  # 1 hour


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_assessments(
    background_tasks: BackgroundTasks,
    force: bool = False,
    api_key_valid: bool = Depends(verify_refresh_api_key),
    db: Session = Depends(get_db)
):
    """
    Refresh assessment catalog
    
    Scrapes the latest assessments from SHL website and updates the vector store.
    Requires API key authentication.
    
    This endpoint:
    1. Scrapes all assessments from the SHL catalog
    2. Saves them to JSON file
    3. Clears the existing vector store
    4. Re-indexes all assessments with new embeddings
    5. Updates the last refresh timestamp
    
    Args:
        force: Force refresh even if recently refreshed
        api_key_valid: API key validation result
        db: Database session
        
    Returns:
        Refresh status and metadata
    """
    global _last_refresh_time, _refresh_in_progress
    
    logger.info("Refresh endpoint called")
    
    # Check if refresh is needed
    if not force and _last_refresh_time:
        time_since_refresh = datetime.utcnow() - _last_refresh_time
        if time_since_refresh < timedelta(hours=1):
            logger.info(f"Refresh skipped - last refresh was {time_since_refresh.total_seconds()/60:.1f} minutes ago")
            return RefreshResponse(
                status="skipped",
                message=f"Refresh skipped - catalog was refreshed {time_since_refresh.total_seconds()/60:.1f} minutes ago. Use force=true to refresh anyway.",
                assessments_count=0,
                timestamp=_last_refresh_time.isoformat()
            )
    
    if _refresh_in_progress:
        logger.warning("Refresh already in progress")
        raise HTTPException(
            status_code=409,
            detail="Refresh already in progress. Please wait for it to complete."
        )
    
    # Perform refresh in background
    background_tasks.add_task(perform_refresh, db)
    
    return RefreshResponse(
        status="started",
        message="Refresh started in background. This may take several minutes.",
        assessments_count=0,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/refresh/status")
async def get_refresh_status(
    api_key_valid: bool = Depends(verify_refresh_api_key),
    db: Session = Depends(get_db)
):
    """
    Get refresh status
    
    Returns information about the last refresh and current status.
    
    Args:
        api_key_valid: API key validation result
        db: Database session
        
    Returns:
        Refresh status information
    """
    global _last_refresh_time, _refresh_in_progress
    
    logger.info("Retrieving refresh status")
    
    try:
        # Get latest metadata from database
        latest_metadata = db.query(VectorStoreMetadata).order_by(
            VectorStoreMetadata.last_updated.desc()
        ).first()
        
        last_update_db = None
        assessments_count_db = 0
        
        if latest_metadata:
            last_update_db = latest_metadata.last_updated.isoformat()
            assessments_count_db = latest_metadata.document_count
        
        # Calculate next auto-refresh time
        next_refresh = None
        if _last_refresh_time:
            next_refresh = (_last_refresh_time + timedelta(days=7)).isoformat()
        
        return {
            "refresh_in_progress": _refresh_in_progress,
            "last_refresh_time": _last_refresh_time.isoformat() if _last_refresh_time else None,
            "last_refresh_db": last_update_db,
            "assessments_count": assessments_count_db,
            "next_auto_refresh": next_refresh,
            "auto_refresh_enabled": _auto_refresh_task is not None,
            "refresh_interval_days": 7
        }
        
    except Exception as e:
        logger.error(f"Failed to get refresh status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get refresh status: {str(e)}"
        )


async def start_auto_refresh():
    """Start the auto-refresh background task"""
    global _auto_refresh_task
    
    if _auto_refresh_task is None:
        _auto_refresh_task = asyncio.create_task(auto_refresh_worker())
        logger.info("Auto-refresh task started")


async def stop_auto_refresh():
    """Stop the auto-refresh background task"""
    global _auto_refresh_task
    
    if _auto_refresh_task:
        _auto_refresh_task.cancel()
        _auto_refresh_task = None
        logger.info("Auto-refresh task stopped")