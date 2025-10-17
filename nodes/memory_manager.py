"""
Memory Manager Node - Saves memory at the end of each turn
"""

from typing import Dict, Any
from core.state import AgentState
from core.state_cleanup import StateCleanupManager


def memory_manager_node(state: AgentState) -> Dict[str, Any]:
    """
    Save memory at the end of each conversation turn
    This node runs last to save all learned information
    """
    print("💾 Memory Manager: Saving memory...")

    try:
        # Initialize state cleanup manager
        cleanup_manager = StateCleanupManager()

        # Clean up state before saving
        if cleanup_manager.should_cleanup(state):
            print("💾 Memory Manager: State cleanup needed, optimizing...")
            cleaned_state = cleanup_manager.cleanup_state(state)
        else:
            cleaned_state = state

        # Get memory manager from state
        memory_manager = state.get("memory_manager")
        if not memory_manager:
            print("💾 Memory Manager: No memory manager found, skipping save")
            return {"next_step": "supervisor"}

        # Save conversation turn with cleaned state
        memory_manager.save_conversation_turn(cleaned_state)
        print("💾 Memory Manager: Saved conversation turn")

        # Update learning patterns
        memory_manager.update_learning_patterns(cleaned_state)
        print("💾 Memory Manager: Updated learning patterns")

        # Save user preferences if any
        if cleaned_state.get("user_preferences"):
            memory_manager.save_user_preferences(cleaned_state)
            print("💾 Memory Manager: Saved user preferences")

        # Clean up old memory files periodically
        cleanup_manager.cleanup_memory_files()

        # Get memory stats
        stats = memory_manager.get_memory_stats()
        print(f"💾 Memory Manager: Memory stats: {stats}")

        return {
            "next_step": "supervisor",
            "memory_saved": True,
            "memory_stats": stats
        }

    except Exception as e:
        print(f"💾 Memory Manager: Error saving memory: {e}")
        return {
            "next_step": "supervisor",
            "memory_saved": False,
            "memory_error": str(e)
        }
