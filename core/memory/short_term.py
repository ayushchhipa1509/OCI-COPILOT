"""
Short-term memory for CloudAgentra
Handles session-based memory and recent context
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class ShortTermMemory:
    """Handles short-term memory for current session"""

    def __init__(self):
        self.session_data = {}
        self.conversation_history = []
        self.recent_actions = []
        self.current_context = {}

    def add_conversation_turn(self, turn_data: Dict[str, Any]):
        """Add a conversation turn to short-term memory"""
        turn_data['timestamp'] = datetime.now().isoformat()
        self.conversation_history.append(turn_data)

        # Keep only last 20 turns in memory
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def get_conversation_context(self) -> Dict[str, Any]:
        """Get current conversation context"""
        return {
            "recent_turns": self.conversation_history[-5:],  # Last 5 turns
            "total_turns": len(self.conversation_history),
            "session_start": self.conversation_history[0]['timestamp'] if self.conversation_history else None
        }

    def add_recent_action(self, action_data: Dict[str, Any]):
        """Add a recent action to memory"""
        action_data['timestamp'] = datetime.now().isoformat()
        self.recent_actions.append(action_data)

        # Keep only last 10 actions
        if len(self.recent_actions) > 10:
            self.recent_actions = self.recent_actions[-10:]

    def get_recent_actions(self) -> List[Dict[str, Any]]:
        """Get recent actions from memory"""
        return self.recent_actions[-5:]  # Last 5 actions

    def update_context(self, context_data: Dict[str, Any]):
        """Update current context"""
        self.current_context.update(context_data)

    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return self.current_context.copy()

    def clear_session(self):
        """Clear session data"""
        self.session_data.clear()
        self.conversation_history.clear()
        self.recent_actions.clear()
        self.current_context.clear()

    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        return {
            "total_conversations": len(self.conversation_history),
            "total_actions": len(self.recent_actions),
            "session_duration": self._calculate_session_duration(),
            "recent_topics": self._extract_recent_topics()
        }

    def _calculate_session_duration(self) -> Optional[str]:
        """Calculate session duration"""
        if not self.conversation_history:
            return None

        start_time = datetime.fromisoformat(
            self.conversation_history[0]['timestamp'])
        end_time = datetime.now()
        duration = end_time - start_time

        return str(duration)

    def _extract_recent_topics(self) -> List[str]:
        """Extract recent topics from conversation"""
        topics = []
        for turn in self.conversation_history[-5:]:
            if 'intent' in turn:
                topics.append(turn['intent'])
        return list(set(topics))  # Remove duplicates

