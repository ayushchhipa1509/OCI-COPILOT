"""
Memory Context Node - Loads memory context at the start of each turn
"""

from typing import Dict, Any
from core.state import AgentState
from core.memory.memory_manager import MemoryManager


def memory_context_node(state: AgentState) -> Dict[str, Any]:
    """
    Load memory context at the start of each conversation turn
    This node runs first to provide context to all other nodes
    """
    print("🧠 Memory Context: Loading memory context...")

    try:
        # Initialize memory manager
        memory_manager = MemoryManager()

        # Get session ID (use query hash as session identifier)
        session_id = f"session_{hash(state.get('query', ''))}"

        # Load all memory context
        memory_context = memory_manager.load_memory_context(session_id)

        # Update state with memory context
        state.update({
            "conversation_context": memory_context.get("conversation_context", {}),
            "user_preferences": memory_context.get("user_preferences", {}),
            "project_context": memory_context.get("project_context", {}),
            "recent_actions": memory_context.get("recent_actions", []),
            "memory_manager": memory_manager,
            "session_id": session_id
        })

        print(f"🧠 Memory Context: Loaded context for session {session_id}")
        print(
            f"🧠 Memory Context: Recent actions: {len(state.get('recent_actions', []))}")
        print(
            f"🧠 Memory Context: User preferences: {len(state.get('user_preferences', {}))}")

        return {
            "next_step": "supervisor",
            **state
        }

    except Exception as e:
        print(f"🧠 Memory Context: Error loading memory context: {e}")
        # Continue without memory context if there's an error
        return {
            "next_step": "supervisor",
            "conversation_context": {},
            "user_preferences": {},
            "project_context": {},
            "recent_actions": [],
            **state
        }

