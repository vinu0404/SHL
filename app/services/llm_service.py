import json
from typing import Dict, Any, Optional, List, Type
import google.generativeai as genai
from pydantic import BaseModel
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("llm_service")


class LLMService:
    """Service for interacting with Gemini LLM"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_output_tokens = settings.GEMINI_MAX_OUTPUT_TOKENS
        self._initialized = False
        self.model = None
    
    def initialize(self):
        """Initialize Gemini API"""
        if self._initialized:
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                }
            )
            self._initialized = True
            logger.info(f"LLM service initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text response from prompt
        
        Args:
            prompt: Input prompt
            system_instruction: Optional system instruction
            temperature: Optional temperature override
            
        Returns:
            Generated text
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # Create model with system instruction if provided
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": temperature or self.temperature,
                        "max_output_tokens": self.max_output_tokens,
                    },
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                logger.warning("Empty response from LLM")
                return ""
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    async def generate_structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: Optional[str] = None,
        max_retries: int = 3
    ) -> BaseModel:
        """
        Generate structured output conforming to a Pydantic schema
        
        Args:
            prompt: Input prompt
            schema: Pydantic model class for output structure
            system_instruction: Optional system instruction
            max_retries: Maximum number of retry attempts
            
        Returns:
            Parsed Pydantic model instance
        """
        if not self._initialized:
            self.initialize()
        
        # Add JSON instruction to prompt
        schema_description = schema.model_json_schema()
        
        structured_prompt = f"""{prompt}

You must respond with ONLY valid JSON matching this exact schema. Do not include any markdown formatting, backticks, or explanatory text.

Schema:
{json.dumps(schema_description, indent=2)}

Return ONLY the JSON object, nothing else."""
        
        for attempt in range(max_retries):
            try:
                response_text = await self.generate_text(
                    structured_prompt,
                    system_instruction=system_instruction
                )
                
                # Clean response
                cleaned_response = self._clean_json_response(response_text)
                
                # Parse JSON
                json_data = json.loads(cleaned_response)
                
                # Validate with Pydantic
                return schema(**json_data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to parse JSON after {max_retries} attempts")
                    raise
            except Exception as e:
                logger.error(f"Structured output generation failed: {e}")
                if attempt == max_retries - 1:
                    raise
        
        raise Exception("Failed to generate structured output")
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response by removing markdown formatting"""
        # Remove markdown code blocks
        response = response.strip()
        
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    async def classify_intent(
        self,
        query: str,
        intents: List[str],
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify query intent
        
        Args:
            query: User query
            intents: List of possible intents
            system_instruction: Optional system instruction
            
        Returns:
            Dictionary with intent and confidence
        """
        prompt = f"""Classify the following query into one of these intents: {', '.join(intents)}

Query: {query}

Analyze the query and determine the most appropriate intent. Consider:
- Is it asking for job-related assessment recommendations?
- Is it a general question about assessments or tests?
- Is it unrelated to assessments?

Respond with JSON in this format:
{{"intent": "<intent>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}}"""
        
        try:
            response = await self.generate_text(prompt, system_instruction)
            cleaned = self._clean_json_response(response)
            result = json.loads(cleaned)
            return result
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Return default
            return {
                "intent": intents[0] if intents else "unknown",
                "confidence": 0.5,
                "reasoning": "Classification failed"
            }
    
    async def extract_information(
        self,
        text: str,
        extraction_schema: Dict[str, str],
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured information from text
        
        Args:
            text: Input text
            extraction_schema: Dictionary describing what to extract
            system_instruction: Optional system instruction
            
        Returns:
            Extracted information
        """
        schema_str = "\n".join([f"- {k}: {v}" for k, v in extraction_schema.items()])
        
        prompt = f"""Extract the following information from the text:

{schema_str}

Text:
{text}

Return the extracted information as JSON."""
        
        try:
            response = await self.generate_text(prompt, system_instruction)
            cleaned = self._clean_json_response(response)
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Information extraction failed: {e}")
            return {}
    
    async def rerank_results(
        self,
        query: str,
        items: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using LLM
        
        Args:
            query: Original query
            items: Items to rerank with 'name' and 'description' fields
            top_k: Number of top items to return
            
        Returns:
            Reranked items with scores
        """
        if not items:
            return []
        
        # Limit items to process
        items_to_process = items[:20]  # Process max 20 items
        
        items_str = "\n\n".join([
            f"ID: {i}\nName: {item.get('name', 'Unknown')}\nDescription: {item.get('description', 'No description')}\nTest Type: {', '.join(item.get('test_type', []))}"
            for i, item in enumerate(items_to_process)
        ])
        
        prompt = f"""Given this query: "{query}"

Rank these assessments from most to least relevant. Consider:
- Alignment with required skills and knowledge
- Match with job requirements
- Test type appropriateness

Assessments:
{items_str}

Return JSON array with rankings:
[{{"id": 0, "score": 0.95, "reason": "..."}}]

Return ONLY the top {top_k} most relevant assessments, ranked by relevance."""
        
        try:
            response = await self.generate_text(prompt)
            cleaned = self._clean_json_response(response)
            rankings = json.loads(cleaned)
            
            # Apply rankings to original items
            ranked_items = []
            for ranking in rankings[:top_k]:
                item_id = ranking.get('id')
                if 0 <= item_id < len(items_to_process):
                    item = items_to_process[item_id].copy()
                    item['llm_score'] = ranking.get('score', 0.5)
                    item['llm_reason'] = ranking.get('reason', '')
                    ranked_items.append(item)
            
            return ranked_items
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Return original items limited to top_k
            return items[:top_k]


# Global LLM service instance
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    if not llm_service._initialized:
        llm_service.initialize()
    return llm_service