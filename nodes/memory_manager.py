"""
Memory Manager Node - Saves memory at the end of each turn
"""

from typing import Dict, Any
from core.state import AgentState


def memory_manager_node(state: AgentState) -> Dict[str, Any]:
    """
    Save memory at the end of each conversation turn
    This node runs last to save all learned information
    """
    print("💾 Memory Manager: Saving memory...")

    try:
        # Get memory manager from state
        memory_manager = state.get("memory_manager")
        if not memory_manager:
            print("💾 Memory Manager: No memory manager found, skipping save")
            return {"next_step": "supervisor"}

        # Save conversation turn
        memory_manager.save_conversation_turn(state)
        print("💾 Memory Manager: Saved conversation turn")

        # Update learning patterns
        memory_manager.update_learning_patterns(state)
        print("💾 Memory Manager: Updated learning patterns")

        # Save user preferences if any
        if state.get("user_preferences"):
            memory_manager.save_user_preferences(state)
            print("💾 Memory Manager: Saved user preferences")

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

