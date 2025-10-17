# core/fast_error_handler.py
"""
Fast LLM-based error handler for each node
"""

import json
from typing import Dict, Any, Optional
from core.llm_manager import call_llm as default_call_llm
from datetime import datetime
import os


class FastErrorHandler:
    """Fast LLM-based error handler for individual nodes"""

    def __init__(self):
        self.learning_file = "memory/error_learning.json"
        self._ensure_learning_file()

    def _ensure_learning_file(self):
        """Ensure learning file exists"""
        os.makedirs("memory", exist_ok=True)
        if not os.path.exists(self.learning_file):
            with open(self.learning_file, 'w') as f:
                json.dump({"successful_patterns": []}, f)

    def handle_error(self, error: Exception, state: Dict[str, Any], node_name: str, call_llm_func=None) -> Dict[str, Any]:
        """
        Fast LLM-based error handling for any node
        """
        if call_llm_func is None:
            call_llm_func = default_call_llm

        # Get user input and context
        user_input = state.get("user_input", "")
        last_node = state.get("last_node", "")

        # Create fast, focused prompt
        prompt = f"""You are a helpful assistant. A user encountered an error while trying to: "{user_input}"

Error: {str(error)}
Node: {node_name}
Previous step: {last_node}

Provide a brief, helpful response (2-3 sentences max):
1. What went wrong in simple terms
2. What they can try instead
3. Whether they should retry

Be friendly and actionable. Don't mention technical details."""

        try:
            # Fast LLM call with minimal context
            messages = [{"role": "user", "content": prompt}]
            llm_response = call_llm_func(state, messages, "fast_error_handler")

            # Extract the response
            error_message = str(llm_response).strip()

            # Simple learning - log if this looks like a good response
            if self._is_good_error_response(error_message):
                self._log_successful_pattern(
                    str(error), error_message, node_name)

            return {
                "error_occurred": True,
                "user_message": error_message,
                "error_type": "llm_analyzed",
                "node": node_name,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as llm_error:
            # Fallback if LLM fails
            return {
                "error_occurred": True,
                "user_message": f"I encountered an issue while processing your request. Please try again or rephrase your request.",
                "error_type": "fallback",
                "node": node_name,
                "timestamp": datetime.now().isoformat()
            }

    def _is_good_error_response(self, response: str) -> bool:
        """Check if the error response is helpful"""
        good_indicators = [
            "try", "instead", "suggest", "help", "alternative",
            "check", "verify", "retry", "again"
        ]
        return any(indicator in response.lower() for indicator in good_indicators)

    def _log_successful_pattern(self, error: str, response: str, node: str):
        """Log successful error handling patterns for learning"""
        try:
            with open(self.learning_file, 'r') as f:
                data = json.load(f)

            # Add new pattern
            pattern = {
                "error": error[:100],  # Truncate for storage
                "response": response[:200],
                "node": node,
                "timestamp": datetime.now().isoformat()
            }

            data["successful_patterns"].append(pattern)

            # Keep only last 50 patterns to prevent file bloat
            if len(data["successful_patterns"]) > 50:
                data["successful_patterns"] = data["successful_patterns"][-50:]

            with open(self.learning_file, 'w') as f:
                json.dump(data, f)

        except Exception:
            # Don't fail if learning fails
            pass

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        try:
            with open(self.learning_file, 'r') as f:
                data = json.load(f)
            return {
                "total_patterns": len(data.get("successful_patterns", [])),
                "recent_patterns": data.get("successful_patterns", [])[-5:]
            }
        except Exception:
            return {"total_patterns": 0, "recent_patterns": []}


# Convenience function for nodes
def handle_node_error(error: Exception, state: Dict[str, Any], node_name: str, call_llm_func=None) -> Dict[str, Any]:
    """
    Fast error handling for any node
    """
    handler = FastErrorHandler()
    return handler.handle_error(error, state, node_name, call_llm_func)
