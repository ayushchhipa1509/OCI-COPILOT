"""
Memory Cache - Handles in-memory caching for fast access
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class MemoryCache:
    """Handles in-memory caching for fast access to memory data"""

    def __init__(self):
        self.conversation_cache = {}
        self.context_cache = {}
        self.user_preferences_cache = {}
        self.project_context_cache = {}
        self.cache_ttl = 300  # 5 minutes TTL

    def get_conversation_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context from cache"""
        if session_id in self.conversation_cache:
            cache_data = self.conversation_cache[session_id]
            if self._is_cache_valid(cache_data.get('timestamp')):
                return cache_data.get('data')
        return None

    def cache_conversation_context(self, session_id: str, data: Dict[str, Any]):
        """Cache conversation context"""
        self.conversation_cache[session_id] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences from cache"""
        if user_id in self.user_preferences_cache:
            cache_data = self.user_preferences_cache[user_id]
            if self._is_cache_valid(cache_data.get('timestamp')):
                return cache_data.get('data')
        return None

    def cache_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Cache user preferences"""
        self.user_preferences_cache[user_id] = {
            'data': preferences,
            'timestamp': datetime.now()
        }

    def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project context from cache"""
        if project_id in self.project_context_cache:
            cache_data = self.project_context_cache[project_id]
            if self._is_cache_valid(cache_data.get('timestamp')):
                return cache_data.get('data')
        return None

    def cache_project_context(self, project_id: str, context: Dict[str, Any]):
        """Cache project context"""
        self.project_context_cache[project_id] = {
            'data': context,
            'timestamp': datetime.now()
        }

    def get_recent_actions(self, session_id: str) -> list:
        """Get recent actions from cache"""
        if session_id in self.context_cache:
            cache_data = self.context_cache[session_id]
            if self._is_cache_valid(cache_data.get('timestamp')):
                return cache_data.get('data', {}).get('recent_actions', [])
        return []

    def cache_recent_actions(self, session_id: str, actions: list):
        """Cache recent actions"""
        if session_id not in self.context_cache:
            self.context_cache[session_id] = {}

        self.context_cache[session_id].update({
            'recent_actions': actions,
            'timestamp': datetime.now()
        })

    def _is_cache_valid(self, timestamp: Optional[datetime]) -> bool:
        """Check if cache entry is still valid"""
        if not timestamp:
            return False

        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return datetime.now() - timestamp < timedelta(seconds=self.cache_ttl)

    def invalidate_cache(self, cache_type: str, identifier: str = None):
        """Invalidate specific cache when data changes"""
        if cache_type == "conversation":
            if identifier:
                self.conversation_cache.pop(identifier, None)
            else:
                self.conversation_cache.clear()

        elif cache_type == "user_preferences":
            if identifier:
                self.user_preferences_cache.pop(identifier, None)
            else:
                self.user_preferences_cache.clear()

        elif cache_type == "project_context":
            if identifier:
                self.project_context_cache.pop(identifier, None)
            else:
                self.project_context_cache.clear()

        elif cache_type == "all":
            self.conversation_cache.clear()
            self.user_preferences_cache.clear()
            self.project_context_cache.clear()
            self.context_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "conversation_cache_size": len(self.conversation_cache),
            "user_preferences_cache_size": len(self.user_preferences_cache),
            "project_context_cache_size": len(self.project_context_cache),
            "context_cache_size": len(self.context_cache),
            "cache_ttl": self.cache_ttl
        }

