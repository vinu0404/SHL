"""
Session handler for managing Chainlit sessions
"""

import sys
from pathlib import Path
import uuid
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.session_service import get_session_service
from app.utils.logger import get_logger

logger = get_logger("session_handler")


class SessionHandler:
    """Handler for managing user sessions in Chainlit"""
    
    def __init__(self):
        self.session_service = get_session_service()
        self.logger = get_logger("session_handler")
        self.session_stats = {}  # In-memory stats for current session
    
    async def create_session(self) -> str:
        """
        Create a new chat session
        
        Returns:
            Session ID
        """
        try:
            session_id = self.session_service.create_session(
                metadata={'source': 'chainlit'}
            )
            
            # Initialize stats
            self.session_stats[session_id] = {
                'total_queries': 0,
                'total_recommendations': 0,
                'query_types': {}
            }
            
            self.logger.info(f"Created new session: {session_id}")
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return str(uuid.uuid4())
    
    async def update_session_stats(self, session_id: str, result: Dict[str, Any]):
        """
        Update session statistics
        
        Args:
            session_id: Session identifier
            result: Result from message processing
        """
        try:
            if session_id not in self.session_stats:
                self.session_stats[session_id] = {
                    'total_queries': 0,
                    'total_recommendations': 0,
                    'query_types': {}
                }
            
            stats = self.session_stats[session_id]
            
            # Update query count
            stats['total_queries'] += 1
            
            # Update query type count
            intent = result.get('intent')
            if intent:
                stats['query_types'][intent] = stats['query_types'].get(intent, 0) + 1
            
            # Update recommendation count
            if result['type'] == 'recommendations':
                stats['total_recommendations'] += result.get('count', 0)
            
            self.logger.debug(f"Updated stats for session {session_id}: {stats}")
            
        except Exception as e:
            self.logger.error(f"Failed to update session stats: {e}")
    
    async def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session statistics
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics or None
        """
        try:
            if session_id in self.session_stats:
                return self.session_stats[session_id].copy()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get session stats: {e}")
            return None
    
    async def end_session(self, session_id: str):
        """
        End a chat session
        
        Args:
            session_id: Session identifier
        """
        try:
            # Clean up in-memory stats
            if session_id in self.session_stats:
                del self.session_stats[session_id]
            
            self.logger.info(f"Ended session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")