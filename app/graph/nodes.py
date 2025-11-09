from typing import Dict, Any
from app.agents import (
    get_supervisor_agent,
    get_jd_extractor_agent,
    get_jd_processor_agent,
    get_rag_agent,
    get_general_query_agent
)
from app.graph.state import GraphState
from app.utils.logger import get_logger
from app.prompts.general_query_prompts import OUT_OF_CONTEXT_RESPONSE

logger = get_logger("graph_nodes")


async def supervisor_node(state: GraphState) -> GraphState:
    """
    Supervisor node - classifies user intent
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with intent classification
    """
    logger.info("Executing supervisor_node")
    
    supervisor = get_supervisor_agent()
    result, _ = await supervisor.run_with_metrics(state)
    
    return result


async def input_check_node(state: GraphState) -> GraphState:
    """
    Input check node - determines if query contains URL
    
    Args:
        state: Current graph state
        
    Returns:
        State (no changes, just routing decision point)
    """
    logger.info("Executing input_check_node")
    
    # This is a decision node, no processing needed
    # The actual URL detection will be done by conditional edge
    
    return state


async def extractor_node(state: GraphState) -> GraphState:
    """
    JD Extractor node - extracts URL and fetches JD
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with extracted JD
    """
    logger.info("Executing extractor_node")
    
    extractor = get_jd_extractor_agent()
    result, _ = await extractor.run_with_metrics(state)
    
    return result


async def processor_node(state: GraphState) -> GraphState:
    """
    JD Processor node - processes and enhances JD/query
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with enhanced query
    """
    logger.info("Executing processor_node")
    
    processor = get_jd_processor_agent()
    result, _ = await processor.run_with_metrics(state)
    
    return result


async def rag_node(state: GraphState) -> GraphState:
    """
    RAG node - retrieves and ranks assessments
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with recommendations
    """
    logger.info("Executing rag_node")
    
    rag = get_rag_agent()
    result, _ = await rag.run_with_metrics(state)
    
    return result


async def general_node(state: GraphState) -> GraphState:
    """
    General query node - handles general questions
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with general answer
    """
    logger.info("Executing general_node")
    
    general = get_general_query_agent()
    result, _ = await general.run_with_metrics(state)
    
    return result


async def error_node(state: GraphState) -> GraphState:
    """
    Error handler node - handles errors in processing
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with error information
    """
    logger.info("Executing error_node")
    
    error_msg = state.get('error_message', 'Unknown error occurred')
    
    logger.error(f"Error in workflow: {error_msg}")
    
    # Provide helpful error message
    state['general_answer'] = (
        f"I apologize, but I encountered an issue processing your request: {error_msg}\n\n"
        "Please try:\n"
        "- Rephrasing your query\n"
        "- Providing more details about your hiring needs\n"
        "- Checking if any URLs are accessible\n"
        "- Starting a new query"
    )
    
    return state


async def end_node(state: GraphState) -> GraphState:
    """
    End node - handles out of context queries
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with redirect message
    """
    logger.info("Executing end_node")
    
    state['general_answer'] = OUT_OF_CONTEXT_RESPONSE
    
    return state


async def format_output_node(state: GraphState) -> GraphState:
    """
    Format output node - final formatting before return
    
    Args:
        state: Current graph state
        
    Returns:
        Formatted state
    """
    logger.info("Executing format_output_node")
    
    # Ensure recommendations are properly formatted
    if state.get('final_recommendations'):
        # Remove any duplicate assessments by URL
        seen_urls = set()
        unique_recommendations = []
        
        for assessment in state['final_recommendations']:
            url = assessment.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_recommendations.append(assessment)
        
        state['final_recommendations'] = unique_recommendations
        
        logger.info(f"Final output: {len(unique_recommendations)} unique recommendations")
    
    return state