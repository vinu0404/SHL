from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.prompts.supervisor_prompts import (
    SUPERVISOR_SYSTEM_INSTRUCTION,
    get_intent_classification_prompt
)
from app.models.schemas import IntentClassification


class SupervisorAgent(BaseAgent):
    """Agent that classifies user intent and routes to appropriate handler"""
    
    def __init__(self):
        super().__init__("supervisor")
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify user intent
        
        Args:
            state: Graph state with 'query' field
            
        Returns:
            Updated state with 'intent' and 'intent_confidence' fields
        """
        query = state.get('query', '')
        
        if not query:
            self.logger.warning("Empty query received")
            return self.update_state(state, {
                'intent': 'out_of_context',
                'intent_confidence': 1.0,
                'error_message': 'Empty query'
            })
        
        self.log_input({'query': query})
        
        try:
            # Generate intent classification prompt
            prompt = get_intent_classification_prompt(query)
            
            # Get classification from LLM
            result = await self.llm_service.generate_structured_output(
                prompt=prompt,
                schema=IntentClassification,
                system_instruction=SUPERVISOR_SYSTEM_INSTRUCTION
            )
            
            self.logger.info(
                f"Classified intent: {result.intent} "
                f"(confidence: {result.confidence:.2f})"
            )
            
            self.log_output({
                'intent': result.intent,
                'confidence': result.confidence,
                'reasoning': result.reasoning
            })
            
            # Update state
            return self.update_state(state, {
                'intent': result.intent,
                'intent_confidence': result.confidence
            })
            
        except Exception as e:
            self.logger.error(f"Intent classification failed: {e}")
            
            # Fallback to simple keyword matching
            intent = self._fallback_classification(query)
            
            return self.update_state(state, {
                'intent': intent,
                'intent_confidence': 0.5,
                'error_message': f'Classification fallback used: {str(e)}'
            })
    
    def _fallback_classification(self, query: str) -> str:
        """
        Simple keyword-based classification fallback
        
        Args:
            query: User query
            
        Returns:
            Intent string
        """
        query_lower = query.lower()
        
        # Check for JD query patterns
        jd_keywords = [
            'hire', 'hiring', 'recruit', 'looking for', 'need', 'seeking',
            'developer', 'engineer', 'manager', 'analyst', 'job description',
            'jd', 'role', 'position', 'candidate', 'assess', 'test'
        ]
        
        if any(keyword in query_lower for keyword in jd_keywords):
            self.logger.info("Fallback classification: jd_query")
            return 'jd_query'
        
        # Check for general query patterns
        general_keywords = [
            'what is', 'tell me', 'explain', 'describe', 'how does',
            'assessment', 'work', 'use', 'available'
        ]
        
        if any(keyword in query_lower for keyword in general_keywords):
            self.logger.info("Fallback classification: general")
            return 'general'
        
        # Default to jd_query if unsure (more useful than out_of_context)
        self.logger.info("Fallback classification: jd_query (default)")
        return 'jd_query'


# Global supervisor agent instance
supervisor_agent = SupervisorAgent()


def get_supervisor_agent() -> SupervisorAgent:
    """Get supervisor agent instance"""
    return supervisor_agent