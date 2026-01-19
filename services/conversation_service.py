"""
Service for managing conversation history and sessions.
"""

import uuid
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation sessions and history."""
    
    def __init__(self):
        """Initialize conversation service with in-memory storage."""
        # In-memory storage: {session_id: [messages]}
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            New session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        logger.info(f"Created new conversation session: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to a conversation session.
        
        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.sessions[session_id].append(message)
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of messages in the conversation
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found, returning empty history")
            return []
        
        return self.sessions[session_id].copy()
    
    def clear_session(self, session_id: str):
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            self.sessions[session_id] = []
            logger.info(f"Cleared conversation history for session {session_id}")
