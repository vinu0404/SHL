from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.schemas import TestTypesResponse
from app.models.assessment import get_all_test_types
from app.database.sqlite_db import get_db
from app.utils.logger import get_logger

logger = get_logger("test_types_route")

router = APIRouter(tags=["utilities"])


@router.get("/test-types", response_model=TestTypesResponse)
async def get_test_types(db: Session = Depends(get_db)):
    """
    Get available test types
    
    Returns information about all available SHL test types.
    
    Args:
        db: Database session
        
    Returns:
        List of test types with descriptions
    """
    logger.info("Retrieving test types")
    
    try:
        test_types = get_all_test_types()
        
        formatted_types = [
            {
                "code": tt.code,
                "name": tt.name,
                "description": tt.description
            }
            for tt in test_types
        ]
        
        logger.info(f"Returning {len(formatted_types)} test types")
        
        return TestTypesResponse(test_types=formatted_types)
        
    except Exception as e:
        logger.error(f"Failed to retrieve test types: {e}")
        # Return empty list on error rather than failing
        return TestTypesResponse(test_types=[])