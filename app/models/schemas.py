from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


# Request Schemas
class RecommendRequest(BaseModel):
    """Request schema for recommendation endpoint"""
    query: str = Field(..., min_length=10, max_length=10000, description="Job description or natural language query")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    session_id: Optional[str] = Field(None, description="Session ID for context")


class ExtractJDRequest(BaseModel):
    """Request schema for JD extraction"""
    url: str = Field(..., description="URL containing job description")


# Response Schemas
class AssessmentResponse(BaseModel):
    """Single assessment response"""
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: Optional[int]
    remote_support: str
    test_type: List[str]
    job_levels: Optional[str] = None  # ADDED
    languages: Optional[str] = None   # ADDED (optional but useful)


class RecommendResponse(BaseModel):
    """Response schema for recommendation endpoint"""
    recommended_assessments: List[AssessmentResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommended_assessments": [
                    {
                        "url": "https://www.shl.com/products/product-catalog/view/python-new/",
                        "name": "Python (New)",
                        "adaptive_support": "No",
                        "description": "Multi-choice test that measures the knowledge of Python programming...",
                        "duration": 11,
                        "remote_support": "Yes",
                        "test_type": ["Knowledge & Skills"],
                        "job_levels": "Entry, Mid, Senior",
                        "languages": "English, Spanish"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy")


class ChatResponse(BaseModel):
    """Chat response"""
    response: str
    session_id: str
    assessments: Optional[List[AssessmentResponse]] = None


class SessionResponse(BaseModel):
    """Session information response"""
    session_id: str
    created_at: str
    interaction_count: int
    interactions: List[Dict[str, Any]]


class TestTypesResponse(BaseModel):
    """Available test types response"""
    test_types: List[Dict[str, str]]


class RefreshResponse(BaseModel):
    """Refresh test database response"""
    status: str
    message: str
    assessments_count: int
    timestamp: str


# Internal Schemas (for agent communication)
class IntentClassification(BaseModel):
    """Intent classification result"""
    intent: str = Field(..., description="Classified intent: jd_query, general, or out_of_context")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(None, description="Reasoning for classification")


class URLExtractionResult(BaseModel):
    """URL extraction result"""
    has_url: bool
    urls: List[str] = Field(default_factory=list)
    primary_url: Optional[str] = None


class JDExtractionResult(BaseModel):
    """Job description extraction result"""
    success: bool
    jd_text: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedQuery(BaseModel):
    """Enhanced query with extracted information"""
    original_query: str
    cleaned_query: str
    extracted_skills: List[str] = Field(default_factory=list)
    extracted_duration: Optional[int] = None
    extracted_job_levels: List[str] = Field(default_factory=list)
    required_test_types: List[str] = Field(default_factory=list)
    key_requirements: List[str] = Field(default_factory=list)


class RAGResult(BaseModel):
    """RAG retrieval result"""
    assessments: List[Dict[str, Any]]
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    test_type_distribution: Dict[str, int] = Field(default_factory=dict)


class GeneralQueryResult(BaseModel):
    """General query answer result"""
    answer: str
    relevant_assessments: Optional[List[Dict[str, Any]]] = None
    sources: List[str] = Field(default_factory=list)


# Graph State Schema
class GraphState(BaseModel):
    """LangGraph state for workflow"""
    # Input
    query: str
    session_id: str
    
    # Intent classification
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    
    # URL extraction
    has_url: bool = False
    extracted_urls: List[str] = Field(default_factory=list)
    
    # JD extraction
    jd_text: Optional[str] = None
    jd_extraction_success: bool = False
    
    # Query enhancement
    enhanced_query: Optional[EnhancedQuery] = None
    
    # RAG results
    retrieved_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    final_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # General query
    general_answer: Optional[str] = None
    
    # Errors
    error_message: Optional[str] = None
    
    # Metadata
    processing_steps: List[str] = Field(default_factory=list)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class AssessmentSearchRequest(BaseModel):
    """Direct assessment search request"""
    search_term: str = Field(..., min_length=1, max_length=200)
    test_type: Optional[str] = None
    duration_max: Optional[int] = None
    remote_only: bool = False
    limit: int = Field(default=10, ge=1, le=50)


class AssessmentSearchResponse(BaseModel):
    """Assessment search response"""
    total_found: int
    assessments: List[AssessmentResponse]