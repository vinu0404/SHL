from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import SessionResponse
from app.database.sqlite_db import get_db
from app.services.session_service import get_session_service
from app.utils.logger import get_logger

logger = get_logger("session_route")

router = APIRouter(tags=["session"])


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get session information and history
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        Session information with interactions
    """
    session_service = get_session_service()
    
    logger.info(f"Retrieving session {session_id}")
    
    try:
        # Get session info
        session_info = session_service.get_session(session_id)
        
        if not session_info:
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Get interactions
        interactions = session_service.get_session_interactions(session_id)
        
        logger.info(f"Found {len(interactions)} interactions for session {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            created_at=session_info['created_at'],
            interaction_count=len(interactions),
            interactions=interactions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a session and all its data
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        Success message
    """
    session_service = get_session_service()
    
    logger.info(f"Deleting session {session_id}")
    
    try:
        success = session_service.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or could not be deleted"
            )
        
        logger.info(f"Session {session_id} deleted successfully")
        
        return {
            "message": f"Session {session_id} deleted successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get("/session/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get session statistics
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        Session statistics
    """
    session_service = get_session_service()
    
    logger.info(f"Retrieving stats for session {session_id}")
    
    try:
        stats = session_service.get_session_stats(session_id)
        
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve session stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session stats: {str(e)}"
        )