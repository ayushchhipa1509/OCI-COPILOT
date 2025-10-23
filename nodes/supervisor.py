from core.fast_error_handler import handle_node_error
from core.llm_manager import call_llm as default_call_llm
from core.prompts import load_prompt
from core.state import AgentState
import re
import json
# nodes/supervisor.py


def _is_retryable_error(error_message: str) -> bool:
    """
    Determine if an error is retryable (code-related) or non-retryable (permission/network).
    """
    if not error_message:
        return False

    error_lower = error_message.lower()

    # Non-retryable errors (permission, network, authentication)
    non_retryable_patterns = [
        "permission denied",
        "not authorized",
        "authentication failed",
        "invalid credentials",
        "network error",
        "connection timeout",
        "service unavailable",
        "rate limit exceeded",
        "quota exceeded"
    ]

    # Check for non-retryable patterns
    for pattern in non_retryable_patterns:
        if pattern in error_lower:
            return False

    # Retryable errors (code-related)
    retryable_patterns = [
        "attributeerror",
        "nameerror",
        "syntaxerror",
        "indentationerror",
        "typeerror",
        "valueerror",
        "keyerror",
        "has no attribute",
        "is not defined",
        "invalid syntax"
    ]

    # Check for retryable patterns
    for pattern in retryable_patterns:
        if pattern in error_lower:
            return True

    # Default to retryable for unknown errors (conservative approach)
    return True


def _llm_based_routing(state: AgentState, call_llm_func) -> dict:
    """
    Use LLM to analyze the current state and make intelligent routing decisions.
    This replaces all the hardcoded logic with LLM-based decision making.
    """
    try:
        # Load the supervisor prompt
        prompt_template = load_prompt('supervisor')

        # Create context for LLM analysis
        context = f"""
You are the intelligent supervisor of an OCI automation agent. Analyze the current state and make routing decisions.

**Current State:**
- Last Node: {state.get('last_node')}
- User Input: {state.get('user_input', '')}
- Next Step (from previous node): {state.get('next_step', 'None')}
- Pending Plan: {state.get('pending_plan', {})}
- Missing Parameters: {state.get('missing_parameters', [])}
- Parameter Gathering Required: {state.get('parameter_gathering_required', False)}
- Confirmation Required: {state.get('confirmation_required', False)}
- Parameter Selection Response: {state.get('parameter_selection_response', '')}
- Confirmation Response: {state.get('confirmation_response', '')}
- Deferred Plan: {state.get('deferred_plan', {})}
- Execution Result: {state.get('execution_result', {})}
- Execution Error: {state.get('execution_error', '')}
- Plan Error: {state.get('plan_error', '')}

**Your Task:**
Analyze this state and determine the next routing step. Consider:
1. If last_node is "planner" and there are missing_parameters, route to presentation_node for parameter gathering
2. If last_node is "planner" and no missing_parameters, route to codegen
3. If user is providing parameters (parameter_selection_response), route to codegen
4. If user is providing confirmation (confirmation_response), route to codegen
5. If there are execution errors, handle appropriately
6. If there are deferred plans, handle resumption

**IMPORTANT:** Respect the flow: normalizer → planner → supervisor → (presentation_node OR codegen)

**Response Format:**
Respond with ONLY a JSON object containing the routing decision.
Example: {{"next_step": "presentation_node", "parameter_gathering_required": true, "missing_parameters": ["compartment_id"]}}
"""

        messages = [
            {"role": "system", "content": context},
            {"role": "user",
                "content": f"Analyze the state and make a routing decision for: {state.get('user_input', 'No input')}"}
        ]

        response = call_llm_func(state, messages, "supervisor")

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            print(f"🧠 LLM Routing Decision: {result}")
            return result
        else:
            # Fallback if JSON parsing fails
            print("⚠️ LLM routing failed to parse JSON, using fallback")
            return {"next_step": "normalizer"}

    except Exception as e:
        print(f"⚠️ LLM routing failed: {e}, using fallback")
        return {"next_step": "normalizer"}


def _analyze_query_routing(user_input: str, call_llm_func, state: dict) -> dict:
    """
    Use LLM to analyze if a query should go directly to presentation node
    or through the normal processing chain.
    """
    try:
        # Load the existing supervisor prompt and adapt it for routing
        prompt_template = load_prompt('supervisor')

        # Create routing-specific context using the supervisor prompt
        routing_context = f"""
You are the supervisor for an OCI automation system. Your task is to analyze the user query and determine the best routing path.

**User Query:** "{user_input}"

**Routing Decision:**
- Route to PRESENTATION_NODE if this is a greeting, OCI knowledge question, or help request
- Route to NORMALIZER if this is an OCI operation that requires API calls

**Response Format:**
Respond with ONLY a JSON object in this exact format:
{{
    "route_to_presentation": true/false,
    "intent": "general_chat" or "oci_question" or "oci_operation",
    "reason": "Brief explanation of routing decision"
}}
"""

        messages = [
            {"role": "system", "content": routing_context},
            {"role": "user", "content": f"Analyze and route this query: {user_input}"}
        ]

        response = call_llm_func(
            state, messages, "supervisor", use_fast_model=True)

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            return result
        else:
            # Fallback if JSON parsing fails
            return {
                "route_to_presentation": False,
                "intent": "oci_operation",
                "reason": "Failed to parse LLM response, defaulting to normalizer"
            }

    except Exception as e:
        print(f"⚠️ Routing analysis failed: {e}, defaulting to normalizer")
        return {
            "route_to_presentation": False,
            "intent": "oci_operation",
            "reason": f"Error in routing analysis: {e}"
        }


def supervisor_node(state: AgentState) -> dict:
    """
    LLM-powered supervisor node - Intelligent routing and state management.
    Uses LLM to analyze context and make intelligent routing decisions.
    """
    # Safety check: Prevent infinite loops
    recursion_count = state.get('recursion_count', 0)
    max_recursion = state.get('max_recursion', 20)

    if recursion_count >= max_recursion:
        print("🚨 RECURSION LIMIT REACHED - FORCING END")
        return {
            "next_step": "presentation_node",
            "presentation": {
                "summary": "I've reached the maximum processing limit. Please try a simpler request or restart the conversation.",
                "format": "chat"
            }
        }

    # Increment recursion counter
    state["recursion_count"] = recursion_count + 1

    print("=" * 60)
    print("🧠 SUPERVISOR NODE - STARTING")
    print(f"Last node was: {state.get('last_node')}")
    print(f"Recursion count: {recursion_count + 1}/{max_recursion}")
    print("=" * 60)

    # Use memory context for intelligent routing
    conversation_context = state.get("conversation_context", {})
    user_preferences = state.get("user_preferences", {})
    recent_actions = state.get("recent_actions", [])

    print(
        f"🧠 SUPERVISOR: Memory context loaded - Recent actions: {len(recent_actions)}")
    print(f"🧠 SUPERVISOR: User preferences: {len(user_preferences)}")
    print(
        f"🧠 SUPERVISOR: Conversation context: {len(conversation_context.get('recent_turns', []))}")

    try:
        # COMPREHENSIVE DEBUG LOGGING
        print(f"🔍 DEBUG: Current state keys: {list(state.keys())}")
        print(f"🔍 DEBUG: user_input: '{state.get('user_input')}'")
        print(f"🔍 DEBUG: last_node: '{state.get('last_node')}'")
        print(f"🔍 DEBUG: next_step: '{state.get('next_step')}'")
        print(
            f"🔍 DEBUG: pending_plan exists: {state.get('pending_plan') is not None}")
        print(
            f"🔍 DEBUG: parameter_gathering_required: {state.get('parameter_gathering_required')}")
        print(
            f"🔍 DEBUG: missing_parameters: {state.get('missing_parameters')}")

        # Use LLM for intelligent routing decisions
        call_llm_func = state.get("call_llm", default_call_llm)

        # If this is the start of the graph, route directly to normalizer
        if state.get("last_node") is None:
            print("🕵️ Entry point: Routing to normalizer for query analysis")
            # Clear any leftover state to ensure fresh start
            state["pending_plan"] = None
            state["missing_parameters"] = None
            state["parameter_gathering_required"] = False
            state["compartment_selection_required"] = False
            state["confirmation_required"] = False
            state["deferred_plan"] = None
            return {"next_step": "normalizer"}

        # Check if normalizer already set a next_step - respect it
        if state.get("next_step") and state.get("last_node") == "normalizer":
            print(
                f"🕵️ Normalizer already routed to: {state.get('next_step')} - respecting decision")
            return {"next_step": state.get("next_step")}

        # If coming from planner, check for missing parameters and route accordingly
        if state.get("last_node") == "planner":
            plan = state.get("plan", {})
            missing_params = plan.get("missing_parameters", [])

            if missing_params:
                print(
                    f"🕵️ Planner identified missing parameters: {missing_params} - routing to presentation_node")
                return {
                    "next_step": "presentation_node",
                    "parameter_gathering_required": True,
                    "missing_parameters": missing_params,
                    "pending_plan": plan
                }
            else:
                print(f"🕵️ Planner completed successfully - routing to codegen")
                return {"next_step": "codegen"}

        # Use LLM to analyze the current state and make routing decisions
        return _llm_based_routing(state, call_llm_func)

    except Exception as e:
        print(f"🚨 SUPERVISOR: Critical error occurred: {e}")

        # Use fast LLM error handler
        call_llm_func = state.get("call_llm", default_call_llm)
        error_response = handle_node_error(
            e, state, "supervisor", call_llm_func)

        return {
            "next_step": "presentation_node",
            "presentation": {
                "summary": error_response['user_message'],
                "format": "chat"
            },
            "error_occurred": True,
            "error_type": error_response['error_type']
        }
