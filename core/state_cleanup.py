# core/state_cleanup.py
"""
State cleanup utilities for managing AgentState lifecycle
"""

from typing import Dict, Any, List
from core.state import AgentState
import time
from datetime import datetime, timedelta


class StateCleanupManager:
    """Manages state cleanup and memory optimization"""

    def __init__(self):
        self.cleanup_fields = [
            'temp_data', 'debug_info', 'processing_flags',
            'intermediate_results', 'cache_data', 'temp_context'
        ]
        self.max_state_size = 50  # Maximum number of fields in state
        self.cleanup_threshold = 0.8  # Cleanup when 80% of max size reached

    def cleanup_state(self, state: AgentState) -> AgentState:
        """
        Remove temporary fields and optimize state size
        """
        print("🧹 State Cleanup: Starting cleanup process...")

        # Remove temporary fields
        cleaned_state = {}
        removed_fields = []

        for key, value in state.items():
            if key in self.cleanup_fields:
                removed_fields.append(key)
                continue

            # Skip None values to reduce state size
            if value is None:
                continue

            # Skip empty collections
            if isinstance(value, (list, dict)) and len(value) == 0:
                continue

            cleaned_state[key] = value

        print(
            f"🧹 State Cleanup: Removed {len(removed_fields)} temporary fields")
        print(
            f"🧹 State Cleanup: State size reduced from {len(state)} to {len(cleaned_state)} fields")

        return cleaned_state

    def should_cleanup(self, state: AgentState) -> bool:
        """
        Determine if state cleanup is needed
        """
        state_size = len(state)
        return state_size > (self.max_state_size * self.cleanup_threshold)

    def cleanup_memory_files(self, memory_dir: str = "memory", days_old: int = 30):
        """
        Clean up old memory files to prevent storage bloat
        """
        import os
        import json

        if not os.path.exists(memory_dir):
            return

        print(
            f"🧹 Memory Cleanup: Cleaning files older than {days_old} days...")

        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_files = 0
        total_size_freed = 0

        for filename in os.listdir(memory_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(memory_dir, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    cleaned_files += 1
                    total_size_freed += file_size
                    print(
                        f"🧹 Memory Cleanup: Removed {filename} ({file_size} bytes)")

        print(
            f"🧹 Memory Cleanup: Cleaned {cleaned_files} files, freed {total_size_freed} bytes")

    def optimize_conversation_history(self, chat_history: List[str], max_entries: int = 50) -> List[str]:
        """
        Optimize conversation history by keeping only recent entries
        """
        if len(chat_history) <= max_entries:
            return chat_history

        # Keep the most recent entries
        optimized_history = chat_history[-max_entries:]

        print(
            f"🧹 History Cleanup: Reduced history from {len(chat_history)} to {len(optimized_history)} entries")

        return optimized_history

    def cleanup_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up session data to prevent memory leaks
        """
        cleaned_data = {}

        for key, value in session_data.items():
            # Skip large objects that aren't essential
            if key in ['raw_llm_responses', 'debug_logs', 'temp_processing']:
                continue

            # Limit size of lists and dictionaries
            if isinstance(value, list) and len(value) > 100:
                cleaned_data[key] = value[-50:]  # Keep last 50 items
            elif isinstance(value, dict) and len(value) > 50:
                # Keep only essential keys
                essential_keys = ['user_input', 'intent', 'action', 'result']
                cleaned_data[key] = {k: v for k,
                                     v in value.items() if k in essential_keys}
            else:
                cleaned_data[key] = value

        return cleaned_data


def cleanup_state(state: AgentState) -> AgentState:
    """
    Convenience function for state cleanup
    """
    cleanup_manager = StateCleanupManager()
    return cleanup_manager.cleanup_state(state)


def should_cleanup_state(state: AgentState) -> bool:
    """
    Convenience function to check if cleanup is needed
    """
    cleanup_manager = StateCleanupManager()
    return cleanup_manager.should_cleanup(state)
