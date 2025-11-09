import uuid
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse, AssessmentResponse
from app.graph.workflow import execute_query
from app.database.sqlite_db import get_db
from app.services.session_service import get_session_service
from app.utils.logger import get_logger
from app.utils.validators import validate_query_length
from app.utils.formatters import format_assessment_response

logger = get_logger("chat_route")

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    General chat/query endpoint
    
    Handles both general questions and job description queries.
    Routes appropriately based on intent.
    
    Args:
        request: Chat request with query and optional session_id
        db: Database session
        
    Returns:
        Chat response with answer and optional assessments
    """
    start_time = time.time()
    session_service = get_session_service()
    
    # Validate query
    is_valid, error_msg = validate_query_length(request.query, min_length=1)
    if not is_valid:
        logger.warning(f"Invalid query: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Use provided session_id or create new one
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"Processing chat request for session {session_id}")
    
    try:
        # Execute workflow
        final_state = await execute_query(request.query, session_id)
        
        # Extract results
        intent = final_state.get('intent')
        recommendations = final_state.get('final_recommendations', [])
        general_answer = final_state.get('general_answer')
        error_message = final_state.get('error_message')
        
        # Build response
        response_text = ""
        assessments = None
        
        if intent == 'jd_query' and recommendations:
            # Job description query with recommendations
            response_text = (
                f"I found {len(recommendations)} relevant assessments for your requirements. "
                "Here are my recommendations:"
            )
            assessments = format_assessment_response(recommendations)
            
        elif intent == 'general' and general_answer:
            # General query
            response_text = general_answer
            
        elif intent == 'out_of_context' and general_answer:
            # Out of context
            response_text = general_answer
            
        elif error_message:
            # Error occurred
            response_text = f"I encountered an issue: {error_message}"
            
        else:
            # Fallback
            response_text = (
                "I processed your query but couldn't generate a specific response. "
                "Please try rephrasing your question or provide more details."
            )
        
        processing_time = time.time() - start_time
        
        # Save interaction to database
        try:
            interaction_id = session_service.save_interaction(
                session_id=session_id,
                query=request.query,
                query_type='chat',
                intent=intent,
                recommended_assessments=assessments if assessments else None,
                processing_time=processing_time,
                error_message=error_message,
                agent_outputs=final_state.get('agent_outputs', {})
            )
            logger.info(f"Saved chat interaction {interaction_id} for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
        
        logger.info(
            f"Chat completed in {processing_time:.2f}s - "
            f"intent: {intent}, assessments: {len(assessments) if assessments else 0}"
        )
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            assessments=assessments
        )
        
    except Exception as e:
        logger.error(f"Chat query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )