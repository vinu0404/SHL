"""
Message handler for processing user queries in Chainlit
"""

import sys
from pathlib import Path
from typing import Dict, Any, Callable, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.graph.workflow import execute_query
from app.utils.logger import get_logger
from app.utils.formatters import format_assessment_response

logger = get_logger("message_handler")


class MessageHandler:
    """Handler for processing user messages"""
    
    def __init__(self):
        self.logger = get_logger("message_handler")
    
    async def handle_message(
        self,
        query: str,
        session_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Handle user message and return structured response
        
        Args:
            query: User query
            session_id: Session identifier
            progress_callback: Optional callback for progress updates
            
        Returns:
            Structured response dictionary
        """
        self.logger.info(f"Handling message for session {session_id}")
        
        try:
            # Update progress - Starting workflow
            if progress_callback:
                await progress_callback("Starting workflow...", 30)
            
            # Execute workflow
            final_state = await execute_query(query, session_id)
            
            # Update progress - Processing results
            if progress_callback:
                await progress_callback("Processing results...", 70)
            
            # Extract results based on intent
            intent = final_state.get('intent')
            
            if intent == 'jd_query':
                result = await self._handle_jd_query_result(final_state, progress_callback)
            elif intent == 'general':
                result = await self._handle_general_result(final_state)
            elif intent == 'out_of_context':
                result = await self._handle_out_of_context_result(final_state)
            else:
                result = self._handle_unknown_result(final_state)
            
            # Update progress - Complete
            if progress_callback:
                await progress_callback("Complete!", 100)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            
            return {
                'type': 'error',
                'message': str(e),
                'intent': None
            }
    
    async def _handle_jd_query_result(
        self,
        final_state: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Handle JD query results"""
        
        recommendations = final_state.get('final_recommendations', [])
        enhanced_query = final_state.get('enhanced_query')
        error_message = final_state.get('error_message')
        
        if error_message:
            return {
                'type': 'error',
                'message': error_message,
                'intent': 'jd_query'
            }
        
        if not recommendations:
            return {
                'type': 'error',
                'message': 'No matching assessments found for your query. Please try rephrasing or providing more details.',
                'intent': 'jd_query'
            }
        
        # Update progress
        if progress_callback:
            await progress_callback("Formatting recommendations...", 90)
        
        # Extract query info for display
        query_info = {}
        
        if enhanced_query:
            query_info = {
                'skills': enhanced_query.extracted_skills,
                'test_types': enhanced_query.required_test_types,
                'duration': enhanced_query.extracted_duration,
                'job_levels': enhanced_query.extracted_job_levels,
                'key_requirements': enhanced_query.key_requirements
            }
        
        return {
            'type': 'recommendations',
            'recommendations': recommendations,
            'query_info': query_info,
            'count': len(recommendations),
            'intent': 'jd_query'
        }
    
    async def _handle_general_result(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general query results"""
        
        general_answer = final_state.get('general_answer', '')
        error_message = final_state.get('error_message')
        
        if error_message:
            return {
                'type': 'error',
                'message': error_message,
                'intent': 'general'
            }
        
        if not general_answer:
            return {
                'type': 'error',
                'message': 'Could not generate a response. Please try rephrasing your question.',
                'intent': 'general'
            }
        
        # Check if there are any assessments mentioned
        related_assessments = []
        retrieved = final_state.get('retrieved_assessments', [])
        
        if retrieved:
            related_assessments = retrieved[:3]  # Show top 3 related assessments
        
        return {
            'type': 'general',
            'answer': general_answer,
            'related_assessments': related_assessments,
            'intent': 'general'
        }
    
    async def _handle_out_of_context_result(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle out of context results"""
        
        general_answer = final_state.get('general_answer', '')
        
        return {
            'type': 'general',
            'answer': general_answer or "I can only help with SHL assessment recommendations and related queries.",
            'related_assessments': [],
            'intent': 'out_of_context'
        }
    
    def _handle_unknown_result(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown intent results"""
        
        return {
            'type': 'error',
            'message': 'Could not determine how to process your query. Please try rephrasing.',
            'intent': None
        }