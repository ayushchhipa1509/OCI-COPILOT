"""
Memory Manager - Orchestrates all memory operations
"""

from typing import Dict, Any, Optional, List
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .store import MemoryStore
from .cache import MemoryCache


class MemoryManager:
    """Orchestrates all memory operations"""

    def __init__(self, store: Optional[MemoryStore] = None, cache: Optional[MemoryCache] = None):
        self.store = store or MemoryStore()
        self.cache = cache or MemoryCache()
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def load_memory_context(self, session_id: str = "default") -> Dict[str, Any]:
        """Load all memory context for a session"""
        context = {}

        # Load conversation context
        context["conversation_context"] = self.get_conversation_context(
            session_id)

        # Load user preferences
        context["user_preferences"] = self.get_user_preferences("default_user")

        # Load project context
        context["project_context"] = self.get_project_context(
            "default_project")

        # Load recent actions
        context["recent_actions"] = self.get_recent_actions(session_id)

        return context

    def get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get conversation context"""
        # Try cache first
        cached_context = self.cache.get_conversation_context(session_id)
        if cached_context:
            return cached_context

        # Load from short-term memory
        context = self.short_term.get_conversation_context()

        # Cache the result
        self.cache.cache_conversation_context(session_id, context)

        return context

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        # Try cache first
        cached_prefs = self.cache.get_user_preferences(user_id)
        if cached_prefs:
            return cached_prefs

        # Load from store
        prefs = self.store.load_user_preferences()
        user_prefs = prefs.get(user_id, {})

        # Cache the result
        self.cache.cache_user_preferences(user_id, user_prefs)

        return user_prefs

    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """Get project context"""
        # Try cache first
        cached_context = self.cache.get_project_context(project_id)
        if cached_context:
            return cached_context

        # Load from long-term memory
        context = self.long_term.get_project_context(project_id)

        # Cache the result
        self.cache.cache_project_context(project_id, context)

        return context

    def get_recent_actions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recent actions"""
        # Try cache first
        cached_actions = self.cache.get_recent_actions(session_id)
        if cached_actions:
            return cached_actions

        # Load from short-term memory
        actions = self.short_term.get_recent_actions()

        # Cache the result
        self.cache.cache_recent_actions(session_id, actions)

        return actions

    def save_conversation_turn(self, state: Dict[str, Any]):
        """Save a conversation turn"""
        # Extract conversation data
        turn_data = {
            "query": state.get("query", ""),
            "intent": state.get("intent", ""),
            "action": state.get("action", ""),
            "parameters": state.get("parameters", {}),
            "result": state.get("result", ""),
            "success": state.get("success", False)
        }

        # Add to short-term memory
        self.short_term.add_conversation_turn(turn_data)

        # Save to store
        self.store.save_conversation_turn(state)

        # Invalidate cache
        self.cache.invalidate_cache("conversation")

    def update_learning_patterns(self, state: Dict[str, Any]):
        """Update learning patterns from state"""
        # Extract learning data
        action = state.get("action", "")
        parameters = state.get("parameters", {})
        success = state.get("success", False)

        if success and action:
            # Learn from successful patterns
            pattern_data = {
                "action": action,
                "parameters": parameters,
                "context": state.get("context", {})
            }

            # Learn global pattern
            self.long_term.learn_from_pattern(action, pattern_data)

            # Learn user-specific pattern
            self.long_term.update_user_pattern(
                "default_user", action, pattern_data)

    def save_user_preferences(self, state: Dict[str, Any]):
        """Save user preferences"""
        # Extract preferences from state
        preferences = state.get("user_preferences", {})
        if preferences:
            self.long_term.update_user_preferences("default_user", preferences)

            # Save to store
            all_prefs = self.store.load_user_preferences()
            all_prefs["default_user"] = preferences
            self.store.save_user_preferences(all_prefs)

            # Invalidate cache
            self.cache.invalidate_cache("user_preferences", "default_user")

    def get_smart_suggestions(self, context: str, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Get smart suggestions based on learned patterns"""
        return self.long_term.get_smart_suggestions(user_id, context)

    def clear_session_memory(self, session_id: str):
        """Clear session-specific memory"""
        self.short_term.clear_session()
        self.cache.invalidate_cache("conversation", session_id)
        self.cache.invalidate_cache("all")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "short_term": self.short_term.get_session_summary(),
            "cache": self.cache.get_cache_stats(),
            "store_files": self._get_store_file_stats()
        }

    def _get_store_file_stats(self) -> Dict[str, Any]:
        """Get store file statistics"""
        import os
        memory_dir = self.store.memory_dir

        stats = {}
        for filename in ["short_term.json", "long_term.json", "user_preferences.json", "conversation_history.json"]:
            filepath = os.path.join(memory_dir, filename)
            if os.path.exists(filepath):
                stats[filename] = {
                    "exists": True,
                    "size": os.path.getsize(filepath)
                }
            else:
                stats[filename] = {"exists": False, "size": 0}

        return stats

