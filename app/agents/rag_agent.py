from typing import Dict, Any, List
from collections import Counter
from app.agents.base_agent import BaseAgent
from app.services.vector_store_service import get_vector_store_service
from app.prompts.rag_prompts import (
    RAG_SYSTEM_INSTRUCTION,
    get_reranking_prompt
)
from app.config import settings
from app.models.schemas import EnhancedQuery


class RAGAgent(BaseAgent):
    """Agent that retrieves and ranks relevant assessments"""
    
    def __init__(self):
        super().__init__("rag")
        self.vector_store = get_vector_store_service()
        self.top_k_retrieve = settings.RAG_TOP_K
        self.min_select = settings.RAG_FINAL_SELECT_MIN
        self.max_select = settings.RAG_FINAL_SELECT_MAX
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve and rank assessments based on enhanced query
        
        Args:
            state: Graph state with 'enhanced_query' field
            
        Returns:
            Updated state with 'retrieved_assessments' and 'final_recommendations'
        """
        enhanced_query = state.get('enhanced_query')
        
        if not enhanced_query:
            self.logger.error("No enhanced query in state")
            return self.update_state(state, {
                'error_message': 'No enhanced query available for RAG'
            })
        
        self.log_input({
            'skills': enhanced_query.extracted_skills,
            'test_types': enhanced_query.required_test_types,
            'duration': enhanced_query.extracted_duration
        })
        
        try:
            # Step 1: Vector search to get initial candidates
            search_query = self._build_search_query(enhanced_query)
            
            self.logger.info(f"Searching with query: {search_query[:100]}...")
            
            retrieved = await self.vector_store.search_assessments(
                query=search_query,
                top_k=self.top_k_retrieve
            )
            
            self.logger.info(f"Retrieved {len(retrieved)} initial candidates")
            
            if not retrieved:
                self.logger.warning("No assessments retrieved from vector search")
                return self.update_state(state, {
                    'retrieved_assessments': [],
                    'final_recommendations': [],
                    'error_message': 'No matching assessments found'
                })
            
            # Step 2: Filter by duration if specified
            if enhanced_query.extracted_duration:
                retrieved = self._filter_by_duration(
                    retrieved,
                    enhanced_query.extracted_duration
                )
                self.logger.info(f"After duration filter: {len(retrieved)} assessments")
            
            # Step 3: LLM reranking for relevance
            reranked = await self._rerank_with_llm(
                retrieved,
                enhanced_query
            )
            
            self.logger.info(f"After LLM reranking: {len(reranked)} assessments")
            
            # Step 4: Apply balance logic if multiple test types needed
            if len(enhanced_query.required_test_types) > 1:
                balanced = self._apply_balance_logic(
                    reranked,
                    enhanced_query.required_test_types
                )
                self.logger.info(f"After balancing: {len(balanced)} assessments")
            else:
                balanced = reranked
            
            # Step 5: Select final recommendations
            final_count = self._determine_final_count(enhanced_query)
            final_recommendations = balanced[:final_count]
            
            self.logger.info(f"Final recommendations: {len(final_recommendations)}")
            
            # Calculate test type distribution
            distribution = self._calculate_test_type_distribution(final_recommendations)
            
            self.log_output({
                'final_count': len(final_recommendations),
                'distribution': distribution
            })
            
            return self.update_state(state, {
                'retrieved_assessments': retrieved,
                'final_recommendations': final_recommendations
            })
            
        except Exception as e:
            self.logger.error(f"RAG execution failed: {e}")
            return self.update_state(state, {
                'retrieved_assessments': [],
                'final_recommendations': [],
                'error_message': f"RAG error: {str(e)}"
            })
    
    def _build_search_query(self, enhanced_query: EnhancedQuery) -> str:
        """Build optimized search query from enhanced query"""
        parts = []
        
        # Add cleaned query
        parts.append(enhanced_query.cleaned_query)
        
        # Add skills
        if enhanced_query.extracted_skills:
            skills_str = ", ".join(enhanced_query.extracted_skills[:10])
            parts.append(f"Required skills: {skills_str}")
        
        # Add test types
        if enhanced_query.required_test_types:
            types_str = ", ".join(enhanced_query.required_test_types)
            parts.append(f"Test types needed: {types_str}")
        
        # Add key requirements
        if enhanced_query.key_requirements:
            req_str = ", ".join(enhanced_query.key_requirements[:5])
            parts.append(f"Key requirements: {req_str}")
        
        return " | ".join(parts)
    
    def _filter_by_duration(
        self,
        assessments: List[Dict[str, Any]],
        max_duration: int
    ) -> List[Dict[str, Any]]:
        """Filter assessments by duration constraint"""
        filtered = []
        
        for assessment in assessments:
            duration = assessment.get('duration')
            
            # Keep if no duration info or within limit
            if duration is None or duration <= max_duration:
                filtered.append(assessment)
        
        return filtered
    
    async def _rerank_with_llm(
        self,
        assessments: List[Dict[str, Any]],
        enhanced_query: EnhancedQuery
    ) -> List[Dict[str, Any]]:
        """Rerank assessments using LLM for better relevance"""
        
        if len(assessments) <= self.max_select:
            # No need to rerank if we have few assessments
            return assessments
        
        try:
            # Prepare assessment text for reranking
            assessments_text = "\n\n".join([
                f"ID: {i}\n"
                f"Name: {a.get('name', 'Unknown')}\n"
                f"Description: {a.get('description', 'No description')}\n"
                f"Test Types: {', '.join(a.get('test_type', []))}\n"
                f"Duration: {a.get('duration', 'Unknown')} minutes\n"
                f"Vector Score: {a.get('similarity_score', 0):.3f}"
                for i, a in enumerate(assessments)
            ])
            
            # Build reranking prompt
            prompt = get_reranking_prompt(
                query=enhanced_query.cleaned_query,
                skills=enhanced_query.extracted_skills,
                test_types=enhanced_query.required_test_types,
                duration_constraint=f"{enhanced_query.extracted_duration} minutes" if enhanced_query.extracted_duration else "None",
                assessments=assessments_text,
                top_k=self.max_select
            )
            
            # Get reranking from LLM
            response = await self.llm_service.generate_text(
                prompt=prompt,
                system_instruction=RAG_SYSTEM_INSTRUCTION
            )
            
            # Parse response
            import json
            cleaned = self.llm_service._clean_json_response(response)
            rankings = json.loads(cleaned)
            
            # Apply rankings
            reranked = []
            for ranking in rankings:
                idx = ranking.get('id')
                if 0 <= idx < len(assessments):
                    assessment = assessments[idx].copy()
                    assessment['llm_score'] = ranking.get('score', 0.5)
                    assessment['llm_reason'] = ranking.get('reason', '')
                    reranked.append(assessment)
            
            return reranked
            
        except Exception as e:
            self.logger.warning(f"LLM reranking failed, using vector scores: {e}")
            # Fall back to vector similarity ranking
            return sorted(
                assessments,
                key=lambda x: x.get('similarity_score', 0),
                reverse=True
            )[:self.max_select]
    
    def _apply_balance_logic(
        self,
        assessments: List[Dict[str, Any]],
        required_test_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Apply balancing logic to ensure diverse test type coverage
        
        This implements the requirement: "If a query spans multiple domains,
        results should contain a balanced mix of assessments"
        """
        if not required_test_types or len(required_test_types) <= 1:
            return assessments
        
        # Group assessments by test type
        type_groups = {}
        for assessment in assessments:
            for test_type in assessment.get('test_type', []):
                if test_type not in type_groups:
                    type_groups[test_type] = []
                type_groups[test_type].append(assessment)
        
        # Calculate target per type
        target_per_type = max(2, self.max_select // len(required_test_types))
        
        # Select balanced set
        balanced = []
        used_urls = set()
        
        # First pass: ensure each required type has representation
        for test_type in required_test_types:
            matching_type = None
            for group_type in type_groups.keys():
                if test_type.lower() in group_type.lower() or group_type.lower() in test_type.lower():
                    matching_type = group_type
                    break
            
            if matching_type and matching_type in type_groups:
                for assessment in type_groups[matching_type][:target_per_type]:
                    if assessment['url'] not in used_urls:
                        balanced.append(assessment)
                        used_urls.add(assessment['url'])
        
        # Second pass: fill remaining slots with highest scored
        remaining = [a for a in assessments if a['url'] not in used_urls]
        remaining.sort(
            key=lambda x: x.get('llm_score', x.get('similarity_score', 0)),
            reverse=True
        )
        
        for assessment in remaining:
            if len(balanced) >= self.max_select:
                break
            balanced.append(assessment)
            used_urls.add(assessment['url'])
        
        return balanced
    
    def _calculate_test_type_distribution(
        self,
        assessments: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate test type distribution"""
        counter = Counter()
        
        for assessment in assessments:
            for test_type in assessment.get('test_type', []):
                counter[test_type] += 1
        
        return dict(counter)
    
    def _determine_final_count(self, enhanced_query: EnhancedQuery) -> int:
        """Determine how many assessments to return"""
        
        # If duration constraint is very tight, return fewer
        if enhanced_query.extracted_duration:
            if enhanced_query.extracted_duration <= 30:
                return self.min_select
            elif enhanced_query.extracted_duration <= 60:
                return min(7, self.max_select)
        
        # If multiple test types needed, return more
        if len(enhanced_query.required_test_types) > 1:
            return self.max_select
        
        # Default
        return min(8, self.max_select)


# Global RAG agent instance
rag_agent = RAGAgent()


def get_rag_agent() -> RAGAgent:
    """Get RAG agent instance"""
    return rag_agent