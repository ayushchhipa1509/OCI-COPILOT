"""
Memory Store - Handles persistent storage of memory data
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class MemoryStore:
    """Handles persistent storage of memory data to JSON files"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = memory_dir
        self.ensure_memory_dir()

    def ensure_memory_dir(self):
        """Ensure memory directory exists"""
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

    def save_short_term(self, data: Dict[str, Any]) -> bool:
        """Save short-term memory to JSON file"""
        try:
            file_path = os.path.join(self.memory_dir, "short_term.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving short-term memory: {e}")
            return False

    def load_short_term(self) -> Dict[str, Any]:
        """Load short-term memory from JSON file"""
        try:
            file_path = os.path.join(self.memory_dir, "short_term.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading short-term memory: {e}")
            return {}

    def save_long_term(self, data: Dict[str, Any]) -> bool:
        """Save long-term memory to JSON file"""
        try:
            file_path = os.path.join(self.memory_dir, "long_term.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving long-term memory: {e}")
            return False

    def load_long_term(self) -> Dict[str, Any]:
        """Load long-term memory from JSON file"""
        try:
            file_path = os.path.join(self.memory_dir, "long_term.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading long-term memory: {e}")
            return {}

    def save_user_preferences(self, data: Dict[str, Any]) -> bool:
        """Save user preferences to JSON file"""
        try:
            file_path = os.path.join(self.memory_dir, "user_preferences.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving user preferences: {e}")
            return False

    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences from JSON file"""
        try:
            file_path = os.path.join(self.memory_dir, "user_preferences.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading user preferences: {e}")
            return {}

    def save_conversation_turn(self, state: Dict[str, Any]) -> bool:
        """Save a conversation turn to memory"""
        try:
            # Extract conversation data from state
            conversation_data = {
                "timestamp": datetime.now().isoformat(),
                "query": state.get("query", ""),
                "intent": state.get("intent", ""),
                "action": state.get("action", ""),
                "parameters": state.get("parameters", {}),
                "result": state.get("result", ""),
                "success": state.get("success", False)
            }

            # Load existing conversation history
            conversation_history = self.load_conversation_history()
            conversation_history.append(conversation_data)

            # Keep only last 50 conversations
            if len(conversation_history) > 50:
                conversation_history = conversation_history[-50:]

            # Save updated history
            file_path = os.path.join(
                self.memory_dir, "conversation_history.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_history, f, indent=2, default=str)

            return True
        except Exception as e:
            print(f"Error saving conversation turn: {e}")
            return False

    def load_conversation_history(self) -> list:
        """Load conversation history from JSON file"""
        try:
            file_path = os.path.join(
                self.memory_dir, "conversation_history.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading conversation history: {e}")
            return []

