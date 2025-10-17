"""
Long-term memory for CloudAgentra
Handles persistent user preferences and project context
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class LongTermMemory:
    """Handles long-term memory for user preferences and project context"""

    def __init__(self):
        self.user_preferences = {}
        self.project_context = {}
        self.learning_patterns = {}
        self.user_patterns = {}

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id].update(preferences)
        self.user_preferences[user_id]['last_updated'] = datetime.now(
        ).isoformat()

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        return self.user_preferences.get(user_id, {})

    def update_project_context(self, project_id: str, context: Dict[str, Any]):
        """Update project context"""
        if project_id not in self.project_context:
            self.project_context[project_id] = {}

        self.project_context[project_id].update(context)
        self.project_context[project_id]['last_updated'] = datetime.now(
        ).isoformat()

    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """Get project context"""
        return self.project_context.get(project_id, {})

    def learn_from_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]):
        """Learn from user patterns"""
        if pattern_type not in self.learning_patterns:
            self.learning_patterns[pattern_type] = []

        pattern_entry = {
            'data': pattern_data,
            'timestamp': datetime.now().isoformat(),
            'frequency': 1
        }

        # Check if similar pattern exists
        for existing_pattern in self.learning_patterns[pattern_type]:
            if self._patterns_similar(existing_pattern['data'], pattern_data):
                existing_pattern['frequency'] += 1
                existing_pattern['last_seen'] = datetime.now().isoformat()
                return

        # Add new pattern
        self.learning_patterns[pattern_type].append(pattern_entry)

    def get_learned_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Get learned patterns"""
        return self.learning_patterns.get(pattern_type, [])

    def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific patterns"""
        return self.user_patterns.get(user_id, {})

    def update_user_pattern(self, user_id: str, pattern_type: str, pattern_data: Dict[str, Any]):
        """Update user-specific pattern"""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {}

        if pattern_type not in self.user_patterns[user_id]:
            self.user_patterns[user_id][pattern_type] = []

        pattern_entry = {
            'data': pattern_data,
            'timestamp': datetime.now().isoformat(),
            'frequency': 1
        }

        # Check if similar pattern exists for this user
        for existing_pattern in self.user_patterns[user_id][pattern_type]:
            if self._patterns_similar(existing_pattern['data'], pattern_data):
                existing_pattern['frequency'] += 1
                existing_pattern['last_seen'] = datetime.now().isoformat()
                return

        # Add new pattern
        self.user_patterns[user_id][pattern_type].append(pattern_entry)

    def get_smart_suggestions(self, user_id: str, context: str) -> List[Dict[str, Any]]:
        """Get smart suggestions based on learned patterns"""
        suggestions = []

        # Get user patterns
        user_patterns = self.get_user_patterns(user_id)

        # Get global patterns
        global_patterns = self.get_learned_patterns(context)

        # Combine and rank suggestions
        all_patterns = []

        for pattern_type, patterns in user_patterns.items():
            for pattern in patterns:
                all_patterns.append({
                    'type': 'user',
                    'pattern_type': pattern_type,
                    'data': pattern['data'],
                    'frequency': pattern['frequency'],
                    'last_seen': pattern.get('last_seen', pattern['timestamp'])
                })

        for pattern in global_patterns:
            all_patterns.append({
                'type': 'global',
                'pattern_type': context,
                'data': pattern['data'],
                'frequency': pattern['frequency'],
                'last_seen': pattern.get('last_seen', pattern['timestamp'])
            })

        # Sort by frequency and recency
        all_patterns.sort(key=lambda x: (
            x['frequency'], x['last_seen']), reverse=True)

        return all_patterns[:5]  # Top 5 suggestions

    def _patterns_similar(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> bool:
        """Check if two patterns are similar"""
        # Simple similarity check - can be enhanced
        common_keys = set(pattern1.keys()) & set(pattern2.keys())
        if len(common_keys) == 0:
            return False

        similarity_score = 0
        for key in common_keys:
            if pattern1[key] == pattern2[key]:
                similarity_score += 1

        # 70% similarity threshold
        return similarity_score / len(common_keys) > 0.7

