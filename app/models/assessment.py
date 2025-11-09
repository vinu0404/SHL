from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class Assessment(BaseModel):
    """Assessment data model"""
    name: str = Field(..., description="Assessment name")
    url: str = Field(..., description="Assessment URL")
    remote_support: str = Field(default="No", description="Remote testing support")
    adaptive_support: str = Field(default="No", description="Adaptive/IRT support")
    test_type: List[str] = Field(default_factory=list, description="Test types")
    description: str = Field(default="", description="Assessment description")
    job_levels: str = Field(default="", description="Target job levels")
    languages: str = Field(default="", description="Available languages")
    duration: Optional[int] = Field(None, description="Duration in minutes")
    
    @validator('test_type', pre=True)
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith('http'):
            raise ValueError("URL must start with http or https")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "url": self.url,
            "remote_support": self.remote_support,
            "adaptive_support": self.adaptive_support,
            "test_type": self.test_type,
            "description": self.description,
            "job_levels": self.job_levels,
            "languages": self.languages,
            "duration": self.duration
        }
    
    def to_embedding_text(self) -> str:
        """Convert assessment to text for embedding"""
        parts = [
            f"Assessment: {self.name}",
            f"Description: {self.description}",
            f"Test Types: {', '.join(self.test_type)}",
            f"Job Levels: {self.job_levels}",
            f"Languages: {self.languages}",
        ]
        
        if self.duration:
            parts.append(f"Duration: {self.duration} minutes")
        
        parts.append(f"Remote Support: {self.remote_support}")
        parts.append(f"Adaptive Support: {self.adaptive_support}")
        
        return " | ".join(parts)
    
    def matches_duration(self, max_duration: Optional[int]) -> bool:
        """Check if assessment matches duration requirement"""
        if max_duration is None:
            return True
        if self.duration is None:
            return True
        return self.duration <= max_duration
    
    def matches_test_type(self, required_types: List[str]) -> bool:
        """Check if assessment matches required test types"""
        if not required_types:
            return True
        
        assessment_types_lower = [t.lower() for t in self.test_type]
        required_types_lower = [t.lower() for t in required_types]
        
        return any(req in assessment_types_lower for req in required_types_lower)
    
    def has_remote_support(self) -> bool:
        """Check if assessment has remote support"""
        return self.remote_support.lower() == "yes"
    
    def has_adaptive_support(self) -> bool:
        """Check if assessment has adaptive support"""
        return self.adaptive_support.lower() == "yes"
    
    def get_primary_test_type(self) -> str:
        """Get primary test type"""
        return self.test_type[0] if self.test_type else "Unknown"


class AssessmentMetadata(BaseModel):
    """Metadata for assessment recommendation"""
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    matching_criteria: List[str] = Field(default_factory=list, description="Matching criteria")
    test_type_match: bool = Field(default=False, description="Test type matches requirement")
    duration_match: bool = Field(default=True, description="Duration matches requirement")
    skill_matches: List[str] = Field(default_factory=list, description="Matching skills")


class AssessmentWithScore(BaseModel):
    """Assessment with relevance score"""
    assessment: Assessment
    metadata: AssessmentMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with score"""
        result = self.assessment.to_dict()
        result["relevance_score"] = self.metadata.relevance_score
        result["matching_criteria"] = self.metadata.matching_criteria
        return result


class TestTypeInfo(BaseModel):
    """Information about a test type"""
    code: str
    name: str
    description: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "K",
                "name": "Knowledge & Skills",
                "description": "Tests that assess technical knowledge and specific skills"
            }
        }


# Test type mappings
TEST_TYPE_MAPPINGS = {
    'A': TestTypeInfo(
        code='A',
        name='Ability & Aptitude',
        description='Tests that measure cognitive abilities and aptitudes'
    ),
    'B': TestTypeInfo(
        code='B',
        name='Biodata & Situational Judgement',
        description='Tests based on biographical data and situational judgment'
    ),
    'C': TestTypeInfo(
        code='C',
        name='Competencies',
        description='Tests that assess behavioral competencies'
    ),
    'D': TestTypeInfo(
        code='D',
        name='Development & 360',
        description='Development assessments and 360-degree feedback tools'
    ),
    'E': TestTypeInfo(
        code='E',
        name='Assessment Exercises',
        description='Practical exercises and work simulations'
    ),
    'K': TestTypeInfo(
        code='K',
        name='Knowledge & Skills',
        description='Tests that assess technical knowledge and specific skills'
    ),
    'P': TestTypeInfo(
        code='P',
        name='Personality & Behavior',
        description='Tests that measure personality traits and behavioral styles'
    ),
    'S': TestTypeInfo(
        code='S',
        name='Simulations',
        description='Interactive simulations of work scenarios'
    )
}


def get_test_type_info(code_or_name: str) -> Optional[TestTypeInfo]:
    """Get test type information by code or name"""
    # Try by code
    if code_or_name in TEST_TYPE_MAPPINGS:
        return TEST_TYPE_MAPPINGS[code_or_name]
    
    # Try by name
    for info in TEST_TYPE_MAPPINGS.values():
        if info.name.lower() == code_or_name.lower():
            return info
    
    return None


def get_all_test_types() -> List[TestTypeInfo]:
    """Get all test type information"""
    return list(TEST_TYPE_MAPPINGS.values())