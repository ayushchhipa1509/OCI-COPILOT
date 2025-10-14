# nodes/supervisor.py
import json
import re
from core.state import AgentState
from core.prompts import load_prompt
from core.llm_manager import call_llm as default_call_llm


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
    Enhanced supervisor node - Smart routing logic.
    - Routes greetings and OCI knowledge questions directly to presentation
    - Routes OCI operations to normalizer for processing
    - Handles exception recovery from verifier
    """
    print("=" * 60)
    print("🧠 SUPERVISOR NODE - STARTING")
    print(f"Last node was: {state.get('last_node')}")
    print("=" * 60)

    # If this is the start of the graph, route directly to normalizer
    if state.get("last_node") is None:
        print("🕵️ Entry point: Routing to normalizer for query analysis")
        return {"next_step": "normalizer"}

    # If called from the planner, check for confirmation requirements or failures
    if state.get("last_node") == "planner":
        plan = state.get("plan")
        plan_error = state.get("plan_error")

        # Check if planner failed to create a plan
        if plan_error or not plan:
            print("🕵️ Supervisor: Planner failed, retrying with Pro model")
            return {
                "next_step": "planner",
                "planner_retry": True,
                "retry_reason": "Plan generation failed"
            }

        # Check for missing parameters first
        missing_params = plan.get("missing_parameters", [])
        print(f"🔍 DEBUG Supervisor: Plan keys: {list(plan.keys())}")
        print(
            f"🔍 DEBUG Supervisor: Missing params from plan: {missing_params}")
        if missing_params:
            print(
                f"🕵️ Supervisor: Missing parameters detected: {missing_params}")

            # Check if we can automatically fetch some parameters
            if "compartment_id" in missing_params:
                print("🕵️ Supervisor: Can auto-fetch compartments, triggering sub-task")
                return {
                    "next_step": "planner",
                    "sub_task": "list_compartments",
                    "pending_plan": plan,
                    "missing_parameters": missing_params,
                    "auto_fetch_required": True
                }
            else:
                return {
                    "next_step": "presentation_node",
                    "parameter_gathering_required": True,
                    "missing_parameters": missing_params,
                    "pending_plan": plan,
                    "gathering_type": "parameter_selection"
                }

        # Check for confirmation requirements
        if plan and plan.get("requires_confirmation"):
            print("🕵️ Supervisor: Mutating action detected, requesting confirmation")
            return {
                "next_step": "presentation_node",
                "confirmation_required": True,
                "pending_plan": plan,
                "confirmation_type": "safety_confirmation"
            }
        else:
            print("🕵️ Supervisor: Safe action, proceeding to codegen")
            return {"next_step": "codegen"}

    # If called from presentation with a confirmation response
    if state.get("last_node") == "presentation_node" and state.get("confirmation_response"):
        response = state.get("confirmation_response", "").lower().strip()
        pending_plan = state.get("pending_plan")

        if response in ["yes", "y", "confirm", "proceed"]:
            print("🕵️ Supervisor: User confirmed action, proceeding to codegen")
            return {
                "next_step": "codegen",
                "plan": pending_plan,
                "confirmation_approved": True
            }
        else:
            print("🕵️ Supervisor: User cancelled action")
            return {
                "next_step": "presentation_node",
                "action_cancelled": True,
                "cancellation_reason": "User declined to proceed with the operation"
            }

    # If called from presentation with parameter selection response
    if state.get("last_node") == "presentation_node" and state.get("parameter_selection_response"):
        from nodes.presentation_node import _parse_parameter_response

        user_input = state.get("parameter_selection_response", "")
        missing_params = state.get("missing_parameters", [])
        pending_plan = state.get("pending_plan")

        # Parse the user's parameter response
        compartment_data = state.get("compartment_data", [])
        selected_params = _parse_parameter_response(
            user_input, missing_params, compartment_data)

        print(f"🕵️ Supervisor: User selected parameters: {selected_params}")

        # Update the plan with selected parameters
        if pending_plan and "params" in pending_plan:
            pending_plan["params"].update(selected_params)
            print(
                f"🕵️ Supervisor: Updated plan with parameters: {pending_plan['params']}")

        # Check if we still need confirmation
        if pending_plan.get("requires_confirmation"):
            print("🕵️ Supervisor: Parameters gathered, now requesting confirmation")
            return {
                "next_step": "presentation_node",
                "confirmation_required": True,
                "pending_plan": pending_plan,
                "confirmation_type": "safety_confirmation"
            }
        else:
            print("🕵️ Supervisor: Parameters gathered, proceeding to codegen")
            return {
                "next_step": "codegen",
                "plan": pending_plan,
                "parameters_updated": True
            }

    # If called from planner with compartment listing result
    if state.get("last_node") == "planner" and state.get("sub_task_result") == "compartment_listing":
        print("🕵️ Supervisor: Compartment listing completed, routing to presentation")
        return {
            "next_step": "presentation_node",
            "compartment_listing_complete": True,
            "pending_plan": state.get("pending_plan"),
            "missing_parameters": state.get("missing_parameters", [])
        }

    # If called from the verifier, handle syntax/static analysis errors
    if state.get("last_node") == "verifier":
        print("🕵️ Supervisor handling VERIFIER failure")

        # Check if the plan is valid first
        plan = state.get("plan")
        plan_valid = state.get("plan_valid", False)

        if not plan or not plan_valid:
            print("🕵️ Supervisor: Invalid plan detected, retrying PLANNER")
            return {
                "next_step": "planner",
                "planner_retry": True,
                "retry_reason": "Plan validation failed"
            }

        # If plan is valid but code failed, retry codegen
        retries = state.get("verify_retries", 0)
        max_retries = 1  # Limit for syntax errors

        if retries < max_retries:
            print(
                f"🔄 Code syntax error detected. Retrying CODEGEN with error context. (Attempt {retries + 1})")
            return {
                "next_step": "codegen",
                "verify_retries": retries + 1,
                "feedback": f"Your previous code failed static verification: {state.get('critique', 'Syntax or structure error')}. Please analyze and fix the code structure.",
                "error_context": "syntax_error"
            }
        else:
            print(
                f"❌ Code failed verification after {max_retries} retries. Giving up.")
            error_message = "I was unable to generate valid code after correction attempts. Please try rephrasing your request."
            return {
                "next_step": "presentation_node",
                "execution_error": error_message
            }

    # If called from the executor, handle runtime errors
    if state.get("last_node") == "executor":
        print("🕵️ Supervisor handling EXECUTOR failure (runtime error)")
        retries = state.get("execution_retries", 0)
        max_retries = 1  # Limit for runtime errors

        # Check if error is retryable (code-related vs permission/network)
        error_message = state.get("execution_error", "")
        is_retryable = _is_retryable_error(error_message)

        if retries < max_retries and is_retryable:
            print(
                f"🔄 Runtime error detected. Retrying CODEGEN with execution context. (Attempt {retries + 1})")
            return {
                "next_step": "codegen",
                "execution_retries": retries + 1,
                "feedback": f"Your previous code failed during execution: {error_message}. Please analyze the error and generate corrected code.",
                "error_context": "runtime_error"
            }
        else:
            if not is_retryable:
                print(f"❌ Non-retryable error detected: {error_message}")
            else:
                print(
                    f"❌ Plan failed execution after {max_retries} retries. Giving up.")
            return {
                "next_step": "presentation_node",
                "execution_error": error_message
            }

    # Default fallback
    print("🕵️ Supervisor in fallback mode. Routing to normalizer.")
    return {"next_step": "normalizer"}
