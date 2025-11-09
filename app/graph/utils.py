from typing import Dict, Any, List
from app.graph.state import GraphState
from app.utils.logger import get_logger

logger = get_logger("graph_utils")


def extract_recommendations_from_state(state: GraphState) -> List[Dict[str, Any]]:
    """
    Extract final recommendations from state
    
    Args:
        state: Graph state
        
    Returns:
        List of recommendations
    """
    return state.get('final_recommendations', [])


def extract_general_answer_from_state(state: GraphState) -> str:
    """
    Extract general answer from state
    
    Args:
        state: Graph state
        
    Returns:
        General answer text
    """
    return state.get('general_answer', '')


def get_state_summary(state: GraphState) -> Dict[str, Any]:
    """
    Get summary of state for logging/debugging
    
    Args:
        state: Graph state
        
    Returns:
        Summary dictionary
    """
    return {
        'intent': state.get('intent'),
        'has_url': state.get('has_url', False),
        'jd_extraction_success': state.get('jd_extraction_success', False),
        'has_enhanced_query': state.get('enhanced_query') is not None,
        'retrieved_count': len(state.get('retrieved_assessments', [])),
        'final_count': len(state.get('final_recommendations', [])),
        'has_general_answer': bool(state.get('general_answer')),
        'has_error': bool(state.get('error_message')),
        'processing_steps': state.get('processing_steps', [])
    }


def is_successful_execution(state: GraphState) -> bool:
    """
    Check if execution was successful
    
    Args:
        state: Graph state
        
    Returns:
        True if successful
    """
    # Check for errors
    if state.get('error_message'):
        return False
    
    # Check for results
    intent = state.get('intent')
    
    if intent == 'jd_query':
        # Should have recommendations
        return len(state.get('final_recommendations', [])) > 0
    elif intent == 'general':
        # Should have general answer
        return bool(state.get('general_answer'))
    
    return True


def get_execution_metrics(state: GraphState) -> Dict[str, Any]:
    """
    Get execution metrics from state
    
    Args:
        state: Graph state
        
    Returns:
        Metrics dictionary
    """
    agent_outputs = state.get('agent_outputs', {})
    
    total_time = sum(
        output.get('execution_time', 0)
        for output in agent_outputs.values()
    )
    
    return {
        'total_execution_time': total_time,
        'agents_executed': len(agent_outputs),
        'processing_steps': len(state.get('processing_steps', [])),
        'success': is_successful_execution(state)
    }


def format_state_for_logging(state: GraphState) -> str:
    """
    Format state for logging
    
    Args:
        state: Graph state
        
    Returns:
        Formatted string
    """
    summary = get_state_summary(state)
    metrics = get_execution_metrics(state)
    
    lines = [
        "=" * 50,
        "Graph State Summary",
        "=" * 50,
        f"Intent: {summary['intent']}",
        f"Has URL: {summary['has_url']}",
        f"JD Extraction: {summary['jd_extraction_success']}",
        f"Enhanced Query: {summary['has_enhanced_query']}",
        f"Retrieved: {summary['retrieved_count']}",
        f"Final Recommendations: {summary['final_count']}",
        f"General Answer: {summary['has_general_answer']}",
        f"Error: {summary['has_error']}",
        "",
        "Metrics:",
        f"Total Time: {metrics['total_execution_time']:.2f}s",
        f"Agents Executed: {metrics['agents_executed']}",
        f"Success: {metrics['success']}",
        "",
        "Processing Steps:",
    ]
    
    for step in summary['processing_steps']:
        lines.append(f"  - {step}")
    
    lines.append("=" * 50)
    
    return "\n".join(lines)