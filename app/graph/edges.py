from typing import Literal
from app.graph.state import GraphState
from app.utils.logger import get_logger
from app.utils.validators import extract_urls_from_text

logger = get_logger("graph_edges")


def route_by_intent(
    state: GraphState
) -> Literal["input_check", "general", "end"]:
    """
    Route based on classified intent
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    intent = state.get('intent', 'jd_query')
    
    logger.info(f"Routing by intent: {intent}")
    
    if intent == 'jd_query':
        return "input_check"
    elif intent == 'general':
        return "general"
    else:  # out_of_context
        return "end"


def has_url(state: GraphState) -> Literal["extractor", "processor"]:
    """
    Check if query contains URL
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    query = state.get('query', '')
    
    # Extract URLs from query
    urls = extract_urls_from_text(query)
    
    has_urls = len(urls) > 0
    
    logger.info(f"URL check: {has_urls} (found {len(urls)} URLs)")
    
    if has_urls:
        return "extractor"
    else:
        return "processor"


def extraction_success(state: GraphState) -> Literal["processor", "error"]:
    """
    Check if JD extraction was successful
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    success = state.get('jd_extraction_success', False)
    
    logger.info(f"JD extraction success: {success}")
    
    if success:
        return "processor"
    else:
        # Even if extraction failed, try to process the original query
        # This is more forgiving than failing completely
        logger.warning("JD extraction failed, but continuing with original query")
        return "processor"


def check_processing_success(state: GraphState) -> Literal["rag", "error"]:
    """
    Check if query processing was successful
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    enhanced_query = state.get('enhanced_query')
    
    if enhanced_query:
        logger.info("Query processing successful, proceeding to RAG")
        return "rag"
    else:
        logger.warning("Query processing failed")
        return "error"


def check_rag_success(state: GraphState) -> Literal["format", "error"]:
    """
    Check if RAG retrieval was successful
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    recommendations = state.get('final_recommendations', [])
    
    if recommendations and len(recommendations) > 0:
        logger.info(f"RAG successful: {len(recommendations)} recommendations")
        return "format"
    else:
        logger.warning("RAG produced no recommendations")
        
        # Check if there's a specific error
        error_msg = state.get('error_message')
        if error_msg:
            return "error"
        
        # If no error but no results, still format output with empty results
        return "format"


def route_general_output(state: GraphState) -> Literal["format"]:
    """
    Route general query output
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name (always format)
    """
    logger.info("Routing general query to format")
    return "format"


def should_continue(state: GraphState) -> bool:
    """
    Check if workflow should continue
    
    Args:
        state: Current graph state
        
    Returns:
        True if should continue, False if should stop
    """
    # Check for critical errors
    error = state.get('error_message')
    
    if error and 'critical' in error.lower():
        logger.error(f"Critical error detected: {error}")
        return False
    
    return True