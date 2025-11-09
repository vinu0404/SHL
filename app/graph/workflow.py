from langgraph.graph import StateGraph, END
from app.graph.state import GraphState, create_initial_state
from app.graph.nodes import (
    supervisor_node,
    input_check_node,
    extractor_node,
    processor_node,
    rag_node,
    general_node,
    error_node,
    end_node,
    format_output_node
)
from app.graph.edges import (
    route_by_intent,
    has_url,
    extraction_success,
    check_processing_success,
    check_rag_success,
    route_general_output
)
from app.utils.logger import get_logger

logger = get_logger("workflow")


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow
    
    This implements the workflow according to the mermaid diagram:
    1. Supervisor classifies intent
    2. Routes to JD query flow, general query, or out of context
    3. JD query flow: check URL -> extract if URL -> process -> RAG -> format
    4. General query flow: answer -> format
    5. Out of context: redirect message
    
    Returns:
        StateGraph workflow
    """
    
    # Create graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("input_check", input_check_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("processor", processor_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("general", general_node)
    workflow.add_node("error", error_node)
    workflow.add_node("end", end_node)
    workflow.add_node("format", format_output_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add edges from supervisor (intent classification routing)
    workflow.add_conditional_edges(
        "supervisor",
        route_by_intent,
        {
            "input_check": "input_check",
            "general": "general",
            "end": "end"
        }
    )
    
    # Add edges from input_check (URL detection routing)
    workflow.add_conditional_edges(
        "input_check",
        has_url,
        {
            "extractor": "extractor",
            "processor": "processor"
        }
    )
    
    # Add edges from extractor (always go to processor after extraction attempt)
    workflow.add_edge("extractor", "processor")
    
    # Add edges from processor (go to RAG if successful)
    workflow.add_edge("processor", "rag")
    
    # Add edges from RAG (go to format)
    workflow.add_edge("rag", "format")
    
    # Add edges from general (go to format)
    workflow.add_edge("general", "format")
    
    # Add edges from error (go to format)
    workflow.add_edge("error", "format")
    
    # Add edges from end (go to format)
    workflow.add_edge("end", "format")
    
    # Format is the final node before END
    workflow.add_edge("format", END)
    
    logger.info("Workflow graph created successfully")
    
    return workflow


class WorkflowExecutor:
    """Executor for the LangGraph workflow"""
    
    def __init__(self):
        self.workflow = create_workflow()
        self.app = self.workflow.compile()
        logger.info("Workflow executor initialized")
    
    async def execute(self, query: str, session_id: str) -> GraphState:
        """
        Execute the workflow for a given query
        
        Args:
            query: User query
            session_id: Session identifier
            
        Returns:
            Final graph state
        """
        logger.info(f"Starting workflow execution for session {session_id}")
        
        try:
            # Create initial state
            initial_state = create_initial_state(query, session_id)
            
            # Execute workflow
            final_state = await self.app.ainvoke(initial_state)
            
            logger.info(f"Workflow execution completed for session {session_id}")
            logger.info(f"Processing steps: {final_state.get('processing_steps', [])}")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Return error state
            error_state = create_initial_state(query, session_id)
            error_state['error_message'] = f"Workflow execution error: {str(e)}"
            error_state['general_answer'] = (
                "I apologize, but I encountered an unexpected error. "
                "Please try again or rephrase your query."
            )
            
            return error_state
    
    async def stream_execute(self, query: str, session_id: str):
        """
        Execute workflow with streaming updates
        
        Args:
            query: User query
            session_id: Session identifier
            
        Yields:
            State updates as they occur
        """
        logger.info(f"Starting streaming workflow execution for session {session_id}")
        
        try:
            # Create initial state
            initial_state = create_initial_state(query, session_id)
            
            # Stream execution
            async for state in self.app.astream(initial_state):
                logger.debug(f"Streaming state update: {list(state.keys())}")
                yield state
            
            logger.info(f"Streaming workflow execution completed for session {session_id}")
            
        except Exception as e:
            logger.error(f"Streaming workflow execution failed: {e}")
            
            # Yield error state
            error_state = create_initial_state(query, session_id)
            error_state['error_message'] = f"Workflow execution error: {str(e)}"
            error_state['general_answer'] = (
                "I apologize, but I encountered an unexpected error. "
                "Please try again or rephrase your query."
            )
            
            yield error_state


# Global workflow executor instance
workflow_executor = WorkflowExecutor()


def get_workflow_executor() -> WorkflowExecutor:
    """Get workflow executor instance"""
    return workflow_executor


async def execute_query(query: str, session_id: str) -> GraphState:
    """
    Convenience function to execute a query
    
    Args:
        query: User query
        session_id: Session identifier
        
    Returns:
        Final graph state
    """
    executor = get_workflow_executor()
    return await executor.execute(query, session_id)


async def stream_query(query: str, session_id: str):
    """
    Convenience function to stream query execution
    
    Args:
        query: User query
        session_id: Session identifier
        
    Yields:
        State updates
    """
    executor = get_workflow_executor()
    async for state in executor.stream_execute(query, session_id):
        yield state