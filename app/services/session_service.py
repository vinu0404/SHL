import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session as DBSession
from app.models.database_models import Session, Interaction, AgentExecution
from app.database.sqlite_db import db_manager
from app.utils.logger import get_logger

logger = get_logger("session_service")


class SessionService:
    """Service for managing user sessions and interactions"""
    
    def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session
        
        Args:
            user_id: Optional user identifier
            metadata: Optional session metadata
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            with db_manager.get_session() as db:
                session = Session(
                    id=session_id,
                    user_id=user_id,
                    session_metadata=metadata or {}  # Changed to session_metadata
                )
                db.add(session)
                db.commit()
            
            logger.info(f"Created session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        try:
            with db_manager.get_session() as db:
                session = db.query(Session).filter(Session.id == session_id).first()
                
                if session:
                    return session.to_dict()
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def save_interaction(
        self,
        session_id: str,
        query: str,
        query_type: str,
        intent: Optional[str] = None,
        recommended_assessments: Optional[List[Dict[str, Any]]] = None,
        processing_time: Optional[float] = None,
        error_message: Optional[str] = None,
        agent_outputs: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Save interaction to database
        
        Args:
            session_id: Session ID
            query: User query
            query_type: Type of query
            intent: Classified intent
            recommended_assessments: List of recommended assessments
            processing_time: Processing time in seconds
            error_message: Error message if any
            agent_outputs: Outputs from various agents
            
        Returns:
            Interaction ID
        """
        try:
            with db_manager.get_session() as db:
                interaction = Interaction(
                    session_id=session_id,
                    query=query,
                    query_type=query_type,
                    intent=intent,
                    recommended_assessments=recommended_assessments,
                    assessment_count=len(recommended_assessments) if recommended_assessments else 0,
                    processing_time=processing_time,
                    error_message=error_message,
                    success=1 if not error_message else 0
                )
                
                # Add agent outputs if provided
                if agent_outputs:
                    if 'supervisor' in agent_outputs:
                        interaction.supervisor_output = agent_outputs['supervisor']
                    if 'jd_extractor' in agent_outputs:
                        interaction.jd_extractor_output = agent_outputs['jd_extractor']
                    if 'jd_processor' in agent_outputs:
                        interaction.jd_processor_output = agent_outputs['jd_processor']
                    if 'rag' in agent_outputs:
                        interaction.rag_output = agent_outputs['rag']
                    if 'general_query' in agent_outputs:
                        interaction.general_query_output = agent_outputs['general_query']
                
                db.add(interaction)
                db.commit()
                db.refresh(interaction)
                
                logger.info(f"Saved interaction {interaction.id} for session {session_id}")
                return interaction.id
                
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            raise
    
    def save_agent_execution(
        self,
        interaction_id: int,
        session_id: str,
        agent_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> int:
        """
        Save agent execution details
        
        Args:
            interaction_id: Interaction ID
            session_id: Session ID
            agent_name: Name of the agent
            input_data: Agent input
            output_data: Agent output
            execution_time: Execution time in seconds
            success: Whether execution was successful
            error_message: Error message if any
            
        Returns:
            Agent execution ID
        """
        try:
            with db_manager.get_session() as db:
                execution = AgentExecution(
                    interaction_id=interaction_id,
                    session_id=session_id,
                    agent_name=agent_name,
                    input_data=input_data,
                    output_data=output_data,
                    execution_time=execution_time,
                    success=1 if success else 0,
                    error_message=error_message
                )
                
                db.add(execution)
                db.commit()
                db.refresh(execution)
                
                return execution.id
                
        except Exception as e:
            logger.error(f"Failed to save agent execution: {e}")
            raise
    
    def get_session_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all interactions for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of interactions
        """
        try:
            with db_manager.get_session() as db:
                interactions = db.query(Interaction).filter(
                    Interaction.session_id == session_id
                ).order_by(Interaction.timestamp).all()
                
                return [interaction.to_dict() for interaction in interactions]
                
        except Exception as e:
            logger.error(f"Failed to get interactions for session {session_id}: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its interactions
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            with db_manager.get_session() as db:
                # Delete agent executions
                db.query(AgentExecution).filter(
                    AgentExecution.session_id == session_id
                ).delete()
                
                # Delete interactions
                db.query(Interaction).filter(
                    Interaction.session_id == session_id
                ).delete()
                
                # Delete session
                db.query(Session).filter(Session.id == session_id).delete()
                
                db.commit()
                
                logger.info(f"Deleted session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Session statistics
        """
        try:
            with db_manager.get_session() as db:
                session = db.query(Session).filter(Session.id == session_id).first()
                
                if not session:
                    return {}
                
                interaction_count = db.query(Interaction).filter(
                    Interaction.session_id == session_id
                ).count()
                
                successful_interactions = db.query(Interaction).filter(
                    Interaction.session_id == session_id,
                    Interaction.success == 1
                ).count()
                
                return {
                    "session_id": session_id,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "total_interactions": interaction_count,
                    "successful_interactions": successful_interactions,
                    "success_rate": successful_interactions / interaction_count if interaction_count > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}


# Global session service instance
session_service = SessionService()


def get_session_service() -> SessionService:
    """Get session service instance"""
    return session_service