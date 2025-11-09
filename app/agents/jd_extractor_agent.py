from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.prompts.jd_extraction_prompts import (
    JD_EXTRACTOR_SYSTEM_INSTRUCTION,
    get_url_extraction_prompt
)
from app.models.schemas import URLExtractionResult
from app.services.jd_fetcher_service import get_jd_fetcher_service
from app.utils.validators import extract_urls_from_text


class JDExtractorAgent(BaseAgent):
    """Agent that extracts URLs and fetches job descriptions"""
    
    def __init__(self):
        super().__init__("jd_extractor")
        self.jd_fetcher = get_jd_fetcher_service()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract URLs from query and fetch JD if URL found
        
        Args:
            state: Graph state with 'query' field
            
        Returns:
            Updated state with URL extraction results and fetched JD
        """
        query = state.get('query', '')
        
        self.log_input({'query': query})
        
        try:
            # First try simple URL extraction
            extracted_urls = extract_urls_from_text(query)
            
            if extracted_urls:
                self.logger.info(f"Found {len(extracted_urls)} URLs using regex")
                
                # Try to fetch JD from the first URL
                primary_url = extracted_urls[0]
                jd_result = await self.jd_fetcher.fetch_jd_from_url(primary_url)
                
                if jd_result['success']:
                    self.logger.info(f"Successfully fetched JD from {primary_url}")
                    
                    return self.update_state(state, {
                        'has_url': True,
                        'extracted_urls': extracted_urls,
                        'jd_text': jd_result['jd_text'],
                        'jd_extraction_success': True
                    })
                else:
                    self.logger.warning(f"Failed to fetch JD: {jd_result['error_message']}")
                    
                    return self.update_state(state, {
                        'has_url': True,
                        'extracted_urls': extracted_urls,
                        'jd_extraction_success': False,
                        'error_message': jd_result['error_message']
                    })
            
            # If no URLs found with regex, try LLM extraction
            self.logger.info("No URLs found with regex, trying LLM extraction")
            
            prompt = get_url_extraction_prompt(query)
            
            result = await self.llm_service.generate_structured_output(
                prompt=prompt,
                schema=URLExtractionResult,
                system_instruction=JD_EXTRACTOR_SYSTEM_INSTRUCTION
            )
            
            if result.has_url and result.urls:
                self.logger.info(f"LLM found URLs: {result.urls}")
                
                # Try to fetch JD from primary URL
                primary_url = result.primary_url or result.urls[0]
                jd_result = await self.jd_fetcher.fetch_jd_from_url(primary_url)
                
                if jd_result['success']:
                    return self.update_state(state, {
                        'has_url': True,
                        'extracted_urls': result.urls,
                        'jd_text': jd_result['jd_text'],
                        'jd_extraction_success': True
                    })
                else:
                    return self.update_state(state, {
                        'has_url': True,
                        'extracted_urls': result.urls,
                        'jd_extraction_success': False,
                        'error_message': jd_result['error_message']
                    })
            
            # No URL found
            self.logger.info("No URLs found in query")
            return self.update_state(state, {
                'has_url': False,
                'extracted_urls': [],
                'jd_extraction_success': False
            })
            
        except Exception as e:
            self.logger.error(f"JD extraction failed: {e}")
            
            return self.update_state(state, {
                'has_url': False,
                'extracted_urls': [],
                'jd_extraction_success': False,
                'error_message': f"JD extraction error: {str(e)}"
            })


# Global JD extractor agent instance
jd_extractor_agent = JDExtractorAgent()


def get_jd_extractor_agent() -> JDExtractorAgent:
    """Get JD extractor agent instance"""
    return jd_extractor_agent