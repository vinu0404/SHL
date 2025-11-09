from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.models.schemas import AssessmentSearchRequest, AssessmentSearchResponse, AssessmentResponse
from app.services.vector_store_service import get_vector_store_service
from app.database.sqlite_db import get_db
from app.utils.logger import get_logger
from app.utils.formatters import format_assessment_response

logger = get_logger("assessments_route")

router = APIRouter(tags=["assessments"])


@router.get("/assessments/search", response_model=AssessmentSearchResponse)
async def search_assessments(
    search_term: str = Query(..., min_length=1, max_length=200, description="Search term"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    duration_max: Optional[int] = Query(None, ge=1, le=300, description="Maximum duration in minutes"),
    remote_only: bool = Query(False, description="Only remote assessments"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    db: Session = Depends(get_db)
):
    """
    Search assessments catalog
    
    Direct search endpoint for finding assessments by keyword.
    
    Args:
        search_term: Search keyword
        test_type: Optional test type filter
        duration_max: Optional maximum duration
        remote_only: Only return remote assessments
        limit: Number of results to return
        db: Database session
        
    Returns:
        Search results
    """
    vector_store = get_vector_store_service()
    
    logger.info(f"Searching assessments: '{search_term}' (limit: {limit})")
    
    try:
        # Build search query
        search_query = search_term
        
        if test_type:
            search_query += f" {test_type}"
        
        # Search vector store
        results = await vector_store.search_assessments(
            query=search_query,
            top_k=limit * 2  # Get more initially for filtering
        )
        
        # Apply filters
        filtered_results = []
        
        for assessment in results:
            # Duration filter
            if duration_max and assessment.get('duration'):
                if assessment['duration'] > duration_max:
                    continue
            
            # Remote filter
            if remote_only and assessment.get('remote_support') != 'Yes':
                continue
            
            # Test type filter
            if test_type:
                assessment_types = [t.lower() for t in assessment.get('test_type', [])]
                if test_type.lower() not in ' '.join(assessment_types):
                    continue
            
            filtered_results.append(assessment)
            
            if len(filtered_results) >= limit:
                break
        
        # Format results
        formatted_results = format_assessment_response(filtered_results)
        
        logger.info(f"Found {len(formatted_results)} matching assessments")
        
        return AssessmentSearchResponse(
            total_found=len(formatted_results),
            assessments=formatted_results
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/assessments/{assessment_id}")
async def get_assessment_details(
    assessment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific assessment details by ID (URL)
    
    Args:
        assessment_id: Assessment identifier (URL-encoded)
        db: Database session
        
    Returns:
        Assessment details
    """
    vector_store = get_vector_store_service()
    
    logger.info(f"Retrieving assessment: {assessment_id}")
    
    try:
        # URL decode if needed
        import urllib.parse
        decoded_url = urllib.parse.unquote(assessment_id)
        
        # Get from vector store
        assessment = await vector_store.get_assessment_by_url(decoded_url)
        
        if not assessment:
            logger.warning(f"Assessment not found: {decoded_url}")
            raise HTTPException(
                status_code=404,
                detail=f"Assessment not found: {assessment_id}"
            )
        
        logger.info(f"Found assessment: {assessment.get('name')}")
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve assessment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve assessment: {str(e)}"
        )


@router.get("/assessments/stats/overview")
async def get_assessments_overview(db: Session = Depends(get_db)):
    """
    Get overview statistics of assessment catalog
    
    Args:
        db: Database session
        
    Returns:
        Catalog statistics
    """
    vector_store = get_vector_store_service()
    
    logger.info("Retrieving assessment catalog overview")
    
    try:
        stats = vector_store.get_collection_stats()
        
        return {
            "total_assessments": stats.get('total_assessments', 0),
            "collection_name": stats.get('collection_name', 'assessments'),
            "last_updated": stats.get('last_updated'),
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve overview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve overview: {str(e)}"
        )