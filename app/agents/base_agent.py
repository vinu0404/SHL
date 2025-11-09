from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import time
from app.services.llm_service import get_llm_service
from app.services.embedding_service import get_embedding_service
from app.utils.logger import get_logger


class BaseAgent(ABC):
    """Base class for all agents with common functionality"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agent.{name}")
        self.llm_service = get_llm_service()
        self.embedding_service = get_embedding_service()
        self.execution_count = 0
    
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state
        """
        pass
    
    async def run_with_metrics(self, state: Dict[str, Any]) -> tuple[Dict[str, Any], float]:
        """
        Execute agent with timing metrics
        
        Args:
            state: Current graph state
            
        Returns:
            Tuple of (updated_state, execution_time)
        """
        start_time = time.time()
        self.execution_count += 1
        
        self.logger.info(f"Starting execution #{self.execution_count}")
        
        try:
            result = await self.execute(state)
            execution_time = time.time() - start_time
            
            self.logger.info(f"Completed in {execution_time:.2f}s")
            
            # Add agent execution info to state
            if 'agent_outputs' not in result:
                result['agent_outputs'] = {}
            
            result['agent_outputs'][self.name] = {
                'execution_time': execution_time,
                'success': True,
                'timestamp': time.time()
            }
            
            # Track processing steps
            if 'processing_steps' not in result:
                result['processing_steps'] = []
            result['processing_steps'].append(f"{self.name} completed")
            
            return result, execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed after {execution_time:.2f}s: {e}")
            
            # Add error to state
            state['error_message'] = f"{self.name} error: {str(e)}"
            
            if 'agent_outputs' not in state:
                state['agent_outputs'] = {}
            
            state['agent_outputs'][self.name] = {
                'execution_time': execution_time,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
            
            return state, execution_time
    
    def log_input(self, data: Dict[str, Any]):
        """Log agent input"""
        self.logger.debug(f"Input: {data}")
    
    def log_output(self, data: Dict[str, Any]):
        """Log agent output"""
        self.logger.debug(f"Output: {data}")
    
    def update_state(
        self,
        state: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update state with new values
        
        Args:
            state: Current state
            updates: Dictionary of updates
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        updated_state.update(updates)
        return updated_state