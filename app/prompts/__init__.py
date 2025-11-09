from app.prompts.supervisor_prompts import (
    SUPERVISOR_SYSTEM_INSTRUCTION,
    get_intent_classification_prompt,
    INTENT_PATTERNS
)
from app.prompts.jd_extraction_prompts import (
    JD_EXTRACTOR_SYSTEM_INSTRUCTION,
    JD_PROCESSOR_SYSTEM_INSTRUCTION,
    get_url_extraction_prompt,
    get_jd_enhancement_prompt,
    get_query_enhancement_prompt
)
from app.prompts.rag_prompts import (
    RAG_SYSTEM_INSTRUCTION,
    get_reranking_prompt,
    get_balance_evaluation_prompt,
    get_assessment_selection_prompt
)
from app.prompts.general_query_prompts import (
    GENERAL_QUERY_SYSTEM_INSTRUCTION,
    get_general_answer_prompt,
    get_assessment_details_prompt,
    get_system_explanation_prompt,
    get_how_to_use_prompt,
    OUT_OF_CONTEXT_RESPONSE,
    get_faq_response
)

__all__ = [
    # Supervisor
    "SUPERVISOR_SYSTEM_INSTRUCTION",
    "get_intent_classification_prompt",
    "INTENT_PATTERNS",
    
    # JD Extraction
    "JD_EXTRACTOR_SYSTEM_INSTRUCTION",
    "JD_PROCESSOR_SYSTEM_INSTRUCTION",
    "get_url_extraction_prompt",
    "get_jd_enhancement_prompt",
    "get_query_enhancement_prompt",
    
    # RAG
    "RAG_SYSTEM_INSTRUCTION",
    "get_reranking_prompt",
    "get_balance_evaluation_prompt",
    "get_assessment_selection_prompt",
    
    # General Query
    "GENERAL_QUERY_SYSTEM_INSTRUCTION",
    "get_general_answer_prompt",
    "get_assessment_details_prompt",
    "get_system_explanation_prompt",
    "get_how_to_use_prompt",
    "OUT_OF_CONTEXT_RESPONSE",
    "get_faq_response",
]