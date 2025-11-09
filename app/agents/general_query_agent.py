from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.services.vector_store_service import get_vector_store_service
from app.prompts.general_query_prompts import (
    GENERAL_QUERY_SYSTEM_INSTRUCTION,
    get_general_answer_prompt,
    get_assessment_details_prompt,
    get_system_explanation_prompt,
    get_faq_response
)
from app.models.assessment import get_all_test_types


class GeneralQueryAgent(BaseAgent):
    """Agent that handles general questions about assessments and the system"""
    
    def __init__(self):
        super().__init__("general_query")
        self.vector_store = get_vector_store_service()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Answer general questions about assessments or the system
        
        Args:
            state: Graph state with 'query' field
            
        Returns:
            Updated state with 'general_answer' field
        """
        query = state.get('query', '')
        
        if not query:
            self.logger.warning("Empty query received")
            return self.update_state(state, {
                'general_answer': 'Please provide a question.',
                'error_message': 'Empty query'
            })
        
        self.log_input({'query': query})
        
        try:
            query_lower = query.lower()
            
            # Check for FAQ matches first
            faq_response = get_faq_response(query_lower)
            if faq_response:
                self.logger.info("Answered using FAQ")
                return self.update_state(state, {
                    'general_answer': faq_response
                })
            
            # Determine query type and handle accordingly
            if self._is_system_question(query_lower):
                answer = await self._handle_system_question(query)
            elif self._is_assessment_specific_question(query_lower):
                answer = await self._handle_assessment_question(query)
            elif self._is_test_type_question(query_lower):
                answer = await self._handle_test_type_question(query)
            else:
                answer = await self._handle_general_question(query)
            
            self.log_output({'answer_length': len(answer)})
            
            return self.update_state(state, {
                'general_answer': answer
            })
            
        except Exception as e:
            self.logger.error(f"General query handling failed: {e}")
            
            fallback_answer = (
                "I apologize, but I encountered an error processing your question. "
                "Please try rephrasing your question or ask about:\n"
                "- How the recommendation system works\n"
                "- Specific SHL assessments\n"
                "- Different types of tests available\n"
                "- How to use this system"
            )
            
            return self.update_state(state, {
                'general_answer': fallback_answer,
                'error_message': f"General query error: {str(e)}"
            })
    
    def _is_system_question(self, query: str) -> bool:
        """Check if question is about the system itself"""
        system_keywords = [
            'how does this work',
            'how do i use',
            'how to use',
            'what can you do',
            'what is this',
            'explain this system',
            'how does the system'
        ]
        return any(keyword in query for keyword in system_keywords)
    
    def _is_assessment_specific_question(self, query: str) -> bool:
        """Check if question is about a specific assessment"""
        specific_keywords = [
            'python test',
            'java assessment',
            'sql test',
            'personality assessment',
            'cognitive test',
            'what is the',
            'tell me about the'
        ]
        return any(keyword in query for keyword in specific_keywords)
    
    def _is_test_type_question(self, query: str) -> bool:
        """Check if question is about test types"""
        test_type_keywords = [
            'test types',
            'types of tests',
            'types of assessments',
            'what types',
            'categories'
        ]
        return any(keyword in query for keyword in test_type_keywords)
    
    async def _handle_system_question(self, query: str) -> str:
        """Handle questions about the system"""
        prompt = get_system_explanation_prompt(query)
        
        answer = await self.llm_service.generate_text(
            prompt=prompt,
            system_instruction=GENERAL_QUERY_SYSTEM_INSTRUCTION
        )
        
        return answer
    
    async def _handle_assessment_question(self, query: str) -> str:
        """Handle questions about specific assessments"""
        
        # Search for relevant assessments
        try:
            assessments = await self.vector_store.search_assessments(
                query=query,
                top_k=5
            )
            
            if assessments:
                # Format assessments for context
                assessments_text = self._format_assessments_for_context(assessments)
                
                prompt = get_assessment_details_prompt(query, assessments_text)
                
                answer = await self.llm_service.generate_text(
                    prompt=prompt,
                    system_instruction=GENERAL_QUERY_SYSTEM_INSTRUCTION
                )
                
                return answer
            else:
                return (
                    "I couldn't find specific information about that assessment in our catalog. "
                    "Could you provide more details or try asking about a different assessment?"
                )
        
        except Exception as e:
            self.logger.error(f"Assessment search failed: {e}")
            return "I encountered an error searching for that assessment. Please try again."
    
    async def _handle_test_type_question(self, query: str) -> str:
        """Handle questions about test types"""
        
        test_types = get_all_test_types()
        
        context = "Available Test Types:\n\n"
        for test_type in test_types:
            context += f"**{test_type.name} ({test_type.code})**\n"
            context += f"{test_type.description}\n\n"
        
        prompt = get_general_answer_prompt(query, context)
        
        answer = await self.llm_service.generate_text(
            prompt=prompt,
            system_instruction=GENERAL_QUERY_SYSTEM_INSTRUCTION
        )
        
        return answer
    
    async def _handle_general_question(self, query: str) -> str:
        """Handle general questions with context from knowledge base"""
        
        # Try to find relevant context
        try:
            assessments = await self.vector_store.search_assessments(
                query=query,
                top_k=3
            )
            
            context = ""
            if assessments:
                context = "Relevant assessments:\n"
                context += self._format_assessments_for_context(assessments)
            
            prompt = get_general_answer_prompt(query, context)
            
            answer = await self.llm_service.generate_text(
                prompt=prompt,
                system_instruction=GENERAL_QUERY_SYSTEM_INSTRUCTION
            )
            
            return answer
            
        except Exception as e:
            self.logger.error(f"General question handling failed: {e}")
            
            # Fallback without context
            prompt = get_general_answer_prompt(query)
            
            answer = await self.llm_service.generate_text(
                prompt=prompt,
                system_instruction=GENERAL_QUERY_SYSTEM_INSTRUCTION
            )
            
            return answer
    
    def _format_assessments_for_context(
        self,
        assessments: List[Dict[str, Any]]
    ) -> str:
        """Format assessments as context for LLM"""
        
        formatted = []
        
        for assessment in assessments:
            text = f"- **{assessment.get('name')}**\n"
            text += f"  Description: {assessment.get('description', 'N/A')}\n"
            text += f"  Test Types: {', '.join(assessment.get('test_type', []))}\n"
            text += f"  Duration: {assessment.get('duration', 'N/A')} minutes\n"
            text += f"  Remote Support: {assessment.get('remote_support', 'N/A')}\n"
            text += f"  Job Levels: {assessment.get('job_levels', 'N/A')}\n"
            formatted.append(text)
        
        return "\n".join(formatted)


# Global general query agent instance
general_query_agent = GeneralQueryAgent()


def get_general_query_agent() -> GeneralQueryAgent:
    """Get general query agent instance"""
    return general_query_agent