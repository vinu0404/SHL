from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Session(Base):
    """User session model"""
    __tablename__ = "sessions"
    
    id = Column(String(100), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(String(100), nullable=True)
    session_metadata = Column(JSON, nullable=True)  # Changed from 'metadata' to 'session_metadata'
    
    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "metadata": self.session_metadata  # Return as 'metadata' for API consistency
        }


class Interaction(Base):
    """User interaction model - stores each query and response"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Input data
    query = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=True)  # 'jd_query', 'general', 'out_of_context'
    
    # Processing data
    intent = Column(String(50), nullable=True)
    extracted_url = Column(String(500), nullable=True)
    extracted_jd = Column(Text, nullable=True)
    enhanced_query = Column(Text, nullable=True)
    
    # Agent outputs
    supervisor_output = Column(JSON, nullable=True)
    jd_extractor_output = Column(JSON, nullable=True)
    jd_processor_output = Column(JSON, nullable=True)
    rag_output = Column(JSON, nullable=True)
    general_query_output = Column(JSON, nullable=True)
    
    # Results
    recommended_assessments = Column(JSON, nullable=True)
    assessment_count = Column(Integer, nullable=True)
    
    # Metadata
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    success = Column(Integer, default=1)  # 1 for success, 0 for failure
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "query": self.query,
            "query_type": self.query_type,
            "intent": self.intent,
            "extracted_url": self.extracted_url,
            "recommended_assessments": self.recommended_assessments,
            "assessment_count": self.assessment_count,
            "processing_time": self.processing_time,
            "error_message": self.error_message,
            "success": bool(self.success)
        }


class AgentExecution(Base):
    """Track individual agent executions"""
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    interaction_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    
    agent_name = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    execution_time = Column(Float, nullable=True)
    success = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "interaction_id": self.interaction_id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "execution_time": self.execution_time,
            "success": bool(self.success),
            "error_message": self.error_message
        }


class AssessmentCache(Base):
    """Cache for assessment data"""
    __tablename__ = "assessment_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    
    data = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Metadata for tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "name": self.name,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


class VectorStoreMetadata(Base):
    """Metadata about vector store updates"""
    __tablename__ = "vector_store_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_name = Column(String(100), nullable=False)
    
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    document_count = Column(Integer, nullable=False)
    
    update_source = Column(String(100), nullable=True)  # 'scraper', 'manual', 'api'
    update_notes = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "collection_name": self.collection_name,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "document_count": self.document_count,
            "update_source": self.update_source,
            "update_notes": self.update_notes
        }