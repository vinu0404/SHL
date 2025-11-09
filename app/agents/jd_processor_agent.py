from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.prompts.jd_extraction_prompts import (
    JD_PROCESSOR_SYSTEM_INSTRUCTION,
    get_jd_enhancement_prompt,
    get_query_enhancement_prompt
)
from app.models.schemas import EnhancedQuery
from app.utils.helpers import (
    extract_skills_from_text,
    extract_duration_from_text,
    extract_job_level_from_text
)


class JDProcessorAgent(BaseAgent):
    """Agent that processes and enhances job descriptions"""
    
    def __init__(self):
        super().__init__("jd_processor")
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process job description and extract structured information
        
        Args:
            state: Graph state with 'query' or 'jd_text' field
            
        Returns:
            Updated state with 'enhanced_query' field
        """
        # Get the text to process (from jd_text if available, otherwise query)
        jd_text = state.get('jd_text') or state.get('query', '')
        
        if not jd_text:
            self.logger.warning("No text to process")
            return self.update_state(state, {
                'error_message': 'No text to process'
            })
        
        self.log_input({'text_length': len(jd_text)})
        
        try:
            # First, try rule-based extraction as baseline
            baseline_skills = extract_skills_from_text(jd_text)
            baseline_duration = extract_duration_from_text(jd_text)
            baseline_job_levels = extract_job_level_from_text(jd_text)
            
            self.logger.info(
                f"Baseline extraction: {len(baseline_skills)} skills, "
                f"duration: {baseline_duration}, "
                f"job levels: {baseline_job_levels}"
            )
            
            # Use LLM for comprehensive extraction
            prompt = get_jd_enhancement_prompt(jd_text)
            
            enhanced = await self.llm_service.generate_structured_output(
                prompt=prompt,
                schema=EnhancedQuery,
                system_instruction=JD_PROCESSOR_SYSTEM_INSTRUCTION
            )
            
            # Merge baseline and LLM results for better coverage
            all_skills = list(set(baseline_skills + enhanced.extracted_skills))
            final_duration = enhanced.extracted_duration or baseline_duration
            all_job_levels = list(set(baseline_job_levels + enhanced.extracted_job_levels))
            
            # Create final enhanced query
            final_enhanced = EnhancedQuery(
                original_query=enhanced.original_query,
                cleaned_query=enhanced.cleaned_query,
                extracted_skills=all_skills,
                extracted_duration=final_duration,
                extracted_job_levels=all_job_levels,
                required_test_types=enhanced.required_test_types,
                key_requirements=enhanced.key_requirements
            )
            
            self.logger.info(
                f"Enhanced extraction: {len(final_enhanced.extracted_skills)} skills, "
                f"{len(final_enhanced.required_test_types)} test types, "
                f"{len(final_enhanced.key_requirements)} key requirements"
            )
            
            self.log_output({
                'skills_count': len(final_enhanced.extracted_skills),
                'test_types': final_enhanced.required_test_types,
                'duration': final_enhanced.extracted_duration
            })
            
            return self.update_state(state, {
                'enhanced_query': final_enhanced
            })
            
        except Exception as e:
            self.logger.error(f"JD processing failed: {e}")
            
            # Create minimal enhanced query with baseline extraction
            fallback_enhanced = EnhancedQuery(
                original_query=jd_text,
                cleaned_query=jd_text[:500],
                extracted_skills=baseline_skills,
                extracted_duration=baseline_duration,
                extracted_job_levels=baseline_job_levels,
                required_test_types=self._infer_test_types(baseline_skills),
                key_requirements=baseline_skills[:5]
            )
            
            return self.update_state(state, {
                'enhanced_query': fallback_enhanced,
                'error_message': f"JD processing error (using fallback): {str(e)}"
            })
    
    def _infer_test_types(self, skills: list) -> list:
        """
        Infer required test types from skills
        
        Args:
            skills: List of extracted skills
            
        Returns:
            List of test type names
        """
        test_types = []
        
        # Technical skills keywords
        technical_keywords = [
            'python', 'java', 'javascript', 'sql', 'c++', 'c#', 'programming',
            'coding', 'software', 'developer', 'engineering', 'technical'
        ]
        
        # Soft skills keywords
        soft_keywords = [
            'communication', 'teamwork', 'leadership', 'collaboration',
            'interpersonal', 'management', 'problem solving'
        ]
        
        skills_text = ' '.join(skills).lower()
        
        if any(keyword in skills_text for keyword in technical_keywords):
            test_types.append('Knowledge & Skills')
        
        if any(keyword in skills_text for keyword in soft_keywords):
            test_types.append('Personality & Behavior')
        
        # Default to both if we have skills but couldn't categorize
        if not test_types and skills:
            test_types = ['Knowledge & Skills', 'Personality & Behavior']
        
        return test_types


# Global JD processor agent instance
jd_processor_agent = JDProcessorAgent()


def get_jd_processor_agent() -> JDProcessorAgent:
    """Get JD processor agent instance"""
    return jd_processor_agent