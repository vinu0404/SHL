from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.sqlite_db import get_db
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("api_dependencies")


async def verify_refresh_api_key(x_api_key: str = Header(...)) -> bool:
    """
    Verify API key for refresh endpoint
    
    Args:
        x_api_key: API key from header
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key != settings.REFRESH_API_KEY:
        logger.warning(f"Invalid API key attempted: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return True


def get_db_session():
    """
    Dependency to get database session
    
    Yields:
        Database session
    """
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()