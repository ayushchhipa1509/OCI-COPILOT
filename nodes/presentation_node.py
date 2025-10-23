# nodes/presentation_node.py
from core.state import AgentState
from core.prompts import load_prompt
from core.llm_manager import call_llm as default_call_llm
from core.fast_error_handler import FastErrorHandler
from typing import Dict, Any, List
import json
# Import the official OCI SDK utility for object-to-dictionary conversion.
from oci.util import to_dict as oci_to_dict


def presentation_node(state: AgentState) -> dict:
    """
    The final node that prepares all data for presentation to the user.
    It uses an LLM to generate intelligent summaries for both RAG and live data.
    Also handles safety confirmation prompts for mutating operations.
    """
    print("=" * 60)
    print("🎬 PRESENTATION NODE - STARTING")
    print("=" * 60)

    # Use memory context for smart suggestions
    conversation_context = state.get("conversation_context", {})
    user_preferences = state.get("user_preferences", {})
    recent_actions = state.get("recent_actions", [])

    print(
        f"🎬 PRESENTATION: Memory context - Recent actions: {len(recent_actions)}")
    print(f"🎬 PRESENTATION: User preferences: {len(user_preferences)}")

    # Handle safety confirmation prompts
    if state.get("confirmation_required"):
        return _handle_safety_confirmation(state)

    # Handle action cancellation
    if state.get("action_cancelled"):
        return _handle_action_cancellation(state)

    # Handle resumption prompt
    if state.get("prompt_for_resumption") and state.get("deferred_plan"):
        return _handle_resumption_prompt(state)

    # Handle parameter gathering
    if state.get("parameter_gathering_required"):
        return _handle_parameter_gathering(state)

    # Handle re-prompt for parameter gathering
    if state.get("re_prompt") and state.get("re_prompt_message"):
        return _handle_re_prompt(state)

    # Handle compartment listing for parameter selection
    if state.get("compartment_listing_complete"):
        return _handle_compartment_selection(state)

    try:
        data_source = state.get("data_source", "live_api")
        user_query = state.get("user_input", "")
        execution_result = state.get("execution_result", {})
        call_llm_func = state.get("call_llm", default_call_llm)

        # Handle plan errors with user-friendly messages
        if state.get("plan_error"):
            return _handle_plan_error(state, call_llm_func)

        if state.get("intent") in ["general_chat", "oci_question"] or state.get("execution_error"):
            summary = state.get("execution_error") or user_query
            if state.get("intent") in ["general_chat", "oci_question"]:
                prompt_template = load_prompt('presentation')
                final_prompt = f"{prompt_template}\n\n## Input Context\n{json.dumps({'user_query': user_query}, default=str)}"
                summary = call_llm_func(
                    state, [{"role": "user", "content": final_prompt}], "final_presentation_chat")
            return {"presentation": {"summary": str(summary).strip(), "format": "chat"}}

        if data_source == "rag_cache":
            print("🎬 PRESENTATION: Processing pre-filtered RAG data")
            try:
                rag_metas = execution_result.get("metadatas", [])
                total_resources = len(rag_metas)

                if total_resources == 0:
                    summary = "I searched the cache, but couldn't find any resources that precisely match your query."
                else:
                    analysis_input = {"data": rag_metas}
                    summary = run_llm_analysis(
                        user_query, analysis_input, call_llm_func, state)

                return {
                    "presentation": {
                        "summary": summary,
                        "format": "table" if total_resources > 0 else "chat",
                        "data": rag_metas,
                        "columns": []
                    }
                }
            except Exception as e:
                return {"presentation": {"summary": f"Error processing cached data: {e}", "format": "chat"}}

        else:
            print("🎬 PRESENTATION: Processing live API data")
            try:
                if isinstance(execution_result, list):
                    normalized_execution_result = {"data": execution_result}
                else:
                    normalized_execution_result = execution_result or {
                        "data": []}

                # Debug: Log the raw data received
                print(
                    f"DEBUG: Raw execution_result type: {type(execution_result)}")
                print(
                    f"DEBUG: Raw execution_result length: {len(execution_result) if isinstance(execution_result, list) else 'Not a list'}")
                print(
                    f"DEBUG: Normalized data length: {len(normalized_execution_result.get('data', []))}")
                if normalized_execution_result.get('data'):
                    print(
                        f"DEBUG: First item keys: {list(normalized_execution_result['data'][0].keys()) if normalized_execution_result['data'] else 'No data'}")

                summary = run_llm_analysis(
                    user_query, normalized_execution_result, call_llm_func, state)
                formatted_data = format_execution_result_for_presentation(
                    normalized_execution_result)

                return {
                    "presentation": {
                        "summary": summary,
                        "format": "table" if formatted_data.get("data") else "chat",
                        "data": formatted_data.get("data", []),
                        "columns": formatted_data.get("columns", [])
                    }
                }
            except Exception as e:
                return {"presentation": {"summary": f"Error processing live data: {e}", "format": "chat"}}

    except Exception as e:
        # Catch any unhandled errors and provide user-friendly message
        print(f"❌ PRESENTATION ERROR: {e}")
        return {
            "presentation": {
                "summary": "I'm experiencing a technical issue right now. Our team is aware of this and working on a fix.\n\nIn the meantime, you can try:\n• **Simple operations**: \"list buckets\", \"list compartments\"\n• **Basic tasks**: \"create a bucket named test-bucket\"\n• **Try again later**: The issue should be resolved soon\n\nSorry for the inconvenience! We're working to improve the system.",
                "format": "chat"
            }
        }

# --- Helper functions for presentation ---


def run_llm_analysis(user_query: str, execution_result: Dict[str, Any], call_llm_func, state: AgentState) -> str:
    """Pass original query + raw data from live execution to LLM for intelligent analysis."""
    try:
        base_prompt = load_prompt("presentation")
    except FileNotFoundError:
        base_prompt = "You are an expert OCI analyst. Analyze OCI data intelligently."

    data_preview = format_data_for_llm(execution_result)
    print(
        f"DEBUG: run_llm_analysis - Data preview length: {len(data_preview)}")
    print(
        f"DEBUG: run_llm_analysis - Data preview preview: {data_preview[:500]}...")

    # Enhanced analysis to show specific requested data
    analysis_prompt = f'''{base_prompt}\n\n## Task:\nAnalyze the following OCI data in context of the user query.\n\nUser Query:\n{user_query}\n\nOCI Data (preview):\n{data_preview}\n\n### Instructions:\n- **IMPORTANT**: Include specific data values that the user is asking for in your response\n- If user asks for "instances with public IP", show the actual public IP addresses\n- If user asks for "security lists with 0.0.0.0", show the specific rules\n- If user asks for "running instances", show instance names, states, and relevant details\n- Always include the actual data values, not just summaries\n- Be specific and show the requested information clearly\n- Summarize your findings and highlight important insights.'''

    messages = [
        {"role": "system", "content": analysis_prompt},
        {"role": "user", "content": f"Answer the query using the data above: {user_query}"}
    ]
    return call_llm_func(state, messages, 'final_presentation_summary')


def format_data_for_llm(execution_result) -> str:
    """Prepare a compact, context-aware JSON preview of the data for the LLM."""
    data = execution_result.get("data", [])
    print(f"DEBUG: format_data_for_llm - Input data length: {len(data)}")

    if not data:
        return "No data items found."

    # --- START OF THE FIX ---

    # 1. Intelligently discover all unique keys from the actual data.
    all_keys = set()
    for item in data:
        if isinstance(item, dict):
            all_keys.update(item.keys())

    # 2. Reuse the existing 'select_important_columns' helper to pick the best keys for a summary.
    #    This makes the function generic and adaptive.
    important_keys = select_important_columns(list(all_keys), data)

    # 3. Build a preview using ONLY the important keys that are actually in the data.
    preview_data = []
    for item in data:
        if isinstance(item, dict):
            # Create a clean dictionary with just the important key-value pairs.
            preview_item = {key: item.get(key) for key in important_keys}
            preview_data.append(preview_item)
        else:
            # Fallback for any non-dictionary items.
            preview_data.append(item)

    # --- END OF THE FIX ---

    # Use default=str to handle complex types like datetime
    result = f"Total items: {len(data)}\nSample: {json.dumps(preview_data, indent=2, default=str)}"
    print(
        f"DEBUG: format_data_for_llm - Preview data length: {len(preview_data)}")
    print(f"DEBUG: format_data_for_llm - Result length: {len(result)}")
    return result


def format_execution_result_for_presentation(execution_result) -> Dict[str, Any]:
    """Convert OCI objects to JSON-serializable format for final presentation."""
    data = execution_result.get("data", [])
    print(
        f"DEBUG: format_execution_result_for_presentation - Input data length: {len(data)}")

    if not data:
        return {"data": [], "columns": [], "summary": "No data found"}

    formatted_data, columns = [], set()

    for item in data:
        try:
            # This single line robustly converts any OCI SDK model object to a clean dictionary.
            item_dict = oci_to_dict(item)

            # Enhanced data extraction for instances with public IP
            if 'id' in item_dict and 'instance' in item_dict.get('id', ''):
                # This is an instance - try to extract public IP information
                item_dict = enhance_instance_data(item_dict)

            formatted_data.append(item_dict)
            columns.update(item_dict.keys())
        except Exception:
            # Fallback for items that are not OCI objects but are already dictionaries (e.g., from RAG).
            if isinstance(item, dict):
                formatted_data.append(item)
                columns.update(item.keys())
            else:
                # If an item cannot be converted, we log a warning and skip it.
                print(
                    f"⚠️ WARNING: Could not convert item of type {type(item)} to a dictionary.")
                continue

    important_columns = select_important_columns(list(columns), formatted_data)
    final_data = [{col: item.get(col) for col in important_columns}
                  for item in formatted_data]

    print(
        f"DEBUG: format_execution_result_for_presentation - Final data length: {len(final_data)}")
    print(
        f"DEBUG: format_execution_result_for_presentation - Final columns: {important_columns}")

    return {"data": final_data, "columns": important_columns, "summary": f"Found {len(final_data)} items"}


def enhance_instance_data(instance_dict):
    """Enhance instance data with public IP information if available."""
    print(
        f"DEBUG: Enhancing instance data for {instance_dict.get('display_name', 'unknown')}")
    print(f"DEBUG: Available keys: {list(instance_dict.keys())}")

    # Check if public IP data is already available (from codegen)
    if 'public_ips' in instance_dict and instance_dict['public_ips']:
        # Public IP data already extracted by codegen
        instance_dict['has_public_ip'] = True
        print(
            f"DEBUG: Found existing public IPs: {instance_dict['public_ips']}")
        return instance_dict

    # Check if we have VNIC information that might contain public IP
    if 'vnic_attachments' in instance_dict:
        public_ips = []
        for vnic_attachment in instance_dict.get('vnic_attachments', []):
            if 'vnic' in vnic_attachment and vnic_attachment['vnic'].get('public_ip'):
                public_ips.append(vnic_attachment['vnic']['public_ip'])

        if public_ips:
            instance_dict['public_ips'] = public_ips
            instance_dict['has_public_ip'] = True
        else:
            instance_dict['has_public_ip'] = False
    else:
        # If no VNIC data and no public IP data, mark as unknown
        if 'has_public_ip' not in instance_dict:
            instance_dict['has_public_ip'] = 'Unknown'

    return instance_dict


def select_important_columns(all_columns: list, data: list) -> list:
    """Select the most important columns for display (max 10)."""
    priority_columns = [
        'display_name', 'name', 'id', 'lifecycle_state', 'state', 'shape', 'size_in_gbs',
        'region', 'availability_domain', 'compartment_id', 'time_created', 'email', 'protocol', 'port',
        'public_ips', 'has_public_ip', 'public_ip'  # Add public IP related columns
    ]
    unwanted_columns = {'attribute_map', 'swagger_types'}

    filtered_columns = [
        col for col in all_columns if col not in unwanted_columns]

    selected = [col for col in priority_columns if col in filtered_columns]
    remaining = [col for col in filtered_columns if col not in selected]

    remaining.sort()

    selected.extend(remaining)

    return selected[:10]


def _handle_safety_confirmation(state: AgentState) -> dict:
    """Handle safety confirmation prompts for mutating operations."""
    pending_plan = state.get("pending_plan", {})
    action = pending_plan.get("action", "unknown action")
    service = pending_plan.get("service", "unknown service")
    params = pending_plan.get("params", {})
    missing_params = pending_plan.get("missing_parameters", [])

    # Build confirmation message
    confirmation_message = f"""
⚠️ **SAFETY CONFIRMATION REQUIRED** ⚠️

I am about to perform a **{action.replace('_', ' ').upper()}** operation in the **{service}** service.

**Operation Details:**
- Action: {action}
- Service: {service}
- Parameters: {json.dumps(params, indent=2)}
"""

    if missing_params:
        confirmation_message += f"""
⚠️ **MISSING PARAMETERS DETECTED:**
The following required parameters are missing: {', '.join(missing_params)}

Please provide the missing information before proceeding.
"""
    else:
        confirmation_message += """
**Are you sure you want to proceed with this operation?**

Type **"yes"** to confirm or **"no"** to cancel.
"""

    return {
        "presentation": {
            "summary": confirmation_message,
            "format": "chat",
            "confirmation_required": True,
            "pending_plan": pending_plan
        }
    }


def _handle_action_cancellation(state: AgentState) -> dict:
    """Handle action cancellation messages."""
    reason = state.get("cancellation_reason", "Operation was cancelled")

    cancellation_message = f"""
❌ **OPERATION CANCELLED**

{reason}

No changes have been made to your OCI environment.
"""

    return {
        "presentation": {
            "summary": cancellation_message,
            "format": "chat"
        }
    }


def _handle_resumption_prompt(state: AgentState) -> dict:
    """Handle prompting user to resume a deferred plan."""
    deferred_plan = state.get("deferred_plan", {})
    action = deferred_plan.get("action", "your previous request")
    service = deferred_plan.get("service", "unknown service")

    # Build the resumption message
    resumption_message = f"""
🔄 **RESUMING YOUR ORIGINAL REQUEST**

You were previously trying to **{action.replace('_', ' ').upper()}** in the **{service}** service.

Would you like to continue with that now? (yes/no)
"""

    return {
        "presentation": {
            "summary": resumption_message,
            "format": "chat",
            "waiting_for_resumption_response": True
        },
        "next_step": "user_input_required"
    }


def _parse_parameter_response(user_input: str, missing_params: list, compartment_data: list = None, call_llm_func=None) -> tuple[bool, dict]:
    """Parse user input to extract parameter values using LLM. Returns (success, selected_params)."""
    selected_params = {}

    # Check if user selected a number for compartment
    if compartment_data and user_input.strip().isdigit():
        selection_num = int(user_input.strip())
        if 1 <= selection_num <= len(compartment_data):
            selected_compartment = compartment_data[selection_num - 1]
            selected_params['compartment_id'] = selected_compartment.get('id')
            print(
                f"🔄 User selected compartment #{selection_num}: {selected_compartment.get('name')}")
            return True, selected_params

    # Use LLM to extract parameters from natural language
    if call_llm_func and missing_params:
        parameter_extraction_prompt = f"""
You are an OCI parameter extractor. Extract the required parameters from the user's natural language response.

User Response: "{user_input}"
Missing Parameters: {missing_params}

Extract the parameters from the user's response. Look for:
- Compartment IDs (any format: ocid1.compartment.oc1.., compartment names, etc.)
- Resource names
- Any other required parameters

Respond with JSON:
{{
    "extracted_parameters": {{"param_name": "value"}},
    "confidence": "high/medium/low",
    "reasoning": "explanation of extraction"
}}
"""

        try:
            # Create a mock state for the LLM call
            mock_state = {"llm_preference": {"provider": "gemini"}}
            response = call_llm_func(mock_state, [
                                     {"role": "user", "content": parameter_extraction_prompt}], "presentation_node")
            import json
            extraction_result = json.loads(response)

            extracted_params = extraction_result.get(
                "extracted_parameters", {})
            confidence = extraction_result.get("confidence", "low")
            reasoning = extraction_result.get("reasoning", "")

            print(f"🧠 LLM Parameter Extraction: {extracted_params}")
            print(f"🧠 Confidence: {confidence}, Reasoning: {reasoning}")

            if extracted_params:
                selected_params.update(extracted_params)
                print(f"🔄 LLM extracted parameters: {selected_params}")
                return True, selected_params

        except Exception as e:
            print(f"🔄 LLM parameter extraction failed: {e}")

    # Fallback to simple parsing if LLM fails
    print("🔄 LLM parsing failed, using fallback parsing")

    # Simple regex-based parsing for key:value pairs
    import re

    # Pattern to match key:value pairs
    pattern = r'(\w+):\s*([^:]+?)(?=\s+\w+:|$)'
    matches = re.findall(pattern, user_input)

    for key, value in matches:
        key = key.strip()
        value = value.strip()
        if key in missing_params:
            selected_params[key] = value
            print(f"🔄 Fallback parsed: {key} = {value}")

    # If still no parameters found, try simple colon splitting
    if not selected_params:
        lines = user_input.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if key in missing_params:
                    selected_params[key] = value
                    print(f"🔄 Fallback parsed (line): {key} = {value}")

    # If no parameters found with colon format, try to extract OCIDs from natural language
    if not selected_params and missing_params:
        import re
        # Look for OCID patterns in the text (simplified pattern)
        ocid_pattern = r'ocid1\.[a-zA-Z0-9._-]+'
        ocids = re.findall(ocid_pattern, user_input)

        if ocids and 'compartment_id' in missing_params:
            # Use the first OCID found as compartment_id
            selected_params['compartment_id'] = ocids[0]
            print(f"🔄 Extracted OCID from natural language: {ocids[0]}")

    # Determine success based on whether we found any parameters
    success = len(selected_params) > 0
    return success, selected_params


def _handle_re_prompt(state: AgentState) -> dict:
    """Handle re-prompting user for parameter information using LLM intelligence."""
    re_prompt_message = state.get(
        "re_prompt_message", "Please provide the required information.")
    missing_params = state.get("missing_parameters", [])
    pending_plan = state.get("pending_plan", {})
    call_llm_func = state.get("call_llm", default_call_llm)

    # Get context for LLM
    action = pending_plan.get("action", "unknown action")
    service = pending_plan.get("service", "unknown service")
    user_query = state.get("user_input", "")

    # Use LLM to generate intelligent re-prompt message
    try:
        re_prompt_prompt = f"""
You are an intelligent OCI assistant helping users provide missing parameters for cloud operations.

Context:
- User Query: "{user_query}"
- Action: {action}
- Service: {service}
- Missing Parameters: {missing_params}
- Re-prompt Reason: {re_prompt_message}

The user's previous response was incomplete or unclear. Generate a helpful, conversational re-prompt message that:
1. Acknowledges their attempt to provide information
2. Clearly explains what's still missing
3. Provides specific, context-aware guidance for each missing parameter
4. Shows relevant examples based on the service type
5. Suggests ways to find the information
6. Makes it feel like a helpful conversation, not a form

Be encouraging and specific about what they need to provide.
"""

        messages = [
            {"role": "system", "content": re_prompt_prompt},
            {"role": "user", "content": f"Generate a re-prompt message for: {action} in {service} service"}
        ]

        enhanced_message = call_llm_func(state, messages, "presentation_node")

        print(
            f"🧠 LLM-generated re-prompt message: {enhanced_message[:200]}...")

    except Exception as e:
        print(f"⚠️ LLM re-prompt failed: {e}, using fallback")

        # Fallback to simple message
        enhanced_message = f"""
⚠️ **{re_prompt_message}**

**Required Information:**
{', '.join(missing_params)}

**Please provide the information in this format:**
compartment_id: ocid1.compartment.oc1..your_compartment_ocid
name: my-resource-name
"""

    return {
        "presentation": {
            "summary": enhanced_message,
            "format": "chat",
            "parameter_gathering_required": True,
            "missing_parameters": missing_params,
            "pending_plan": pending_plan
        }
    }


def _handle_parameter_gathering(state: AgentState) -> dict:
    """Handle parameter gathering for deployment operations using LLM intelligence."""
    pending_plan = state.get("pending_plan", {})
    missing_params = state.get("missing_parameters", [])
    call_llm_func = state.get("call_llm", default_call_llm)

    # Get context for LLM
    action = pending_plan.get("action", "unknown action")
    service = pending_plan.get("service", "unknown service")
    user_query = state.get("user_input", "")

    # Check if we're resuming after completing a prerequisite
    is_resuming = state.get("resumed_after_prerequisite", False)

    # Use LLM to generate intelligent parameter gathering message
    try:
        parameter_gathering_prompt = f"""
You are an intelligent OCI assistant helping users provide missing parameters for cloud operations.

Context:
- User Query: "{user_query}"
- Action: {action}
- Service: {service}
- Missing Parameters: {missing_params}
- Is Resuming: {is_resuming}

Generate a helpful, conversational message that:
1. Explains what operation they're trying to perform
2. Clearly identifies what information is still needed
3. Provides context-aware guidance for each missing parameter
4. Shows relevant examples based on the service type
5. Suggests ways to find the information (like "list compartments")
6. Makes it feel like a helpful conversation, not a form

Be specific about why each parameter is needed and provide service-appropriate examples.
"""

        messages = [
            {"role": "system", "content": parameter_gathering_prompt},
            {"role": "user", "content": f"Generate a parameter gathering message for: {action} in {service} service"}
        ]

        gathering_message = call_llm_func(state, messages, "presentation_node")

        print(
            f"🧠 LLM-generated parameter gathering message: {gathering_message[:200]}...")

    except Exception as e:
        print(f"⚠️ LLM parameter gathering failed: {e}, using fallback")

        # Fallback to simple message
        gathering_message = f"""
🔧 **PARAMETER GATHERING REQUIRED**

I need additional information to complete your **{action.replace('_', ' ').upper()}** operation in the **{service}** service.

**Missing Parameters:** {', '.join(missing_params)}

Please provide the missing information in this format:
compartment_id: ocid1.compartment.oc1..your_compartment_ocid
"""

    return {
        "presentation": {
            "summary": gathering_message,
            "format": "chat",
            "parameter_gathering_required": True,
            "missing_parameters": missing_params,
            "pending_plan": pending_plan
        },
        "next_step": "user_input_required"  # CRITICAL: Signal that we need user input
    }


def _handle_compartment_selection(state: AgentState) -> dict:
    """Handle compartment selection using LLM intelligence."""
    pending_plan = state.get("pending_plan", {})
    missing_params = state.get("missing_parameters", [])
    action = pending_plan.get("action", "unknown action")
    service = pending_plan.get("service", "unknown service")
    call_llm_func = state.get("call_llm", default_call_llm)

    # Get the execution result (compartment list)
    execution_result = state.get("execution_result", {})
    compartment_data = execution_result.get("data", [])

    # Use LLM to generate intelligent compartment selection message
    try:
        compartment_selection_prompt = f"""
You are an intelligent OCI assistant helping users select compartments for cloud operations.

Context:
- Action: {action}
- Service: {service}
- Available Compartments: {len(compartment_data)} compartments found
- Compartment Data: {compartment_data[:3] if compartment_data else "None"}

Generate a helpful, conversational message that:
1. Explains why compartment selection is needed
2. If compartments are available, presents them in a user-friendly numbered list
3. If no compartments found, explains how to provide the OCID manually
4. Provides clear instructions on how to respond
5. Makes it feel like a helpful conversation

Be specific about the operation they're trying to perform and why compartment selection matters.
"""

        messages = [
            {"role": "system", "content": compartment_selection_prompt},
            {"role": "user", "content": f"Generate a compartment selection message for: {action} in {service} service"}
        ]

        selection_message = call_llm_func(state, messages, "presentation_node")

        print(
            f"🧠 LLM-generated compartment selection message: {selection_message[:200]}...")

    except Exception as e:
        print(f"⚠️ LLM compartment selection failed: {e}, using fallback")

        # Fallback to simple message
        if not compartment_data:
            selection_message = f"""
🔧 **COMPARTMENT SELECTION REQUIRED**

I need to know which compartment to use for your **{action.replace('_', ' ').upper()}** operation in the **{service}** service.

Unfortunately, I couldn't retrieve the list of compartments. Please provide the compartment OCID manually:

**Example Response:**
compartment_id: ocid1.compartment.oc1..your_compartment_ocid
"""
        else:
            selection_message = f"""
🔧 **COMPARTMENT SELECTION REQUIRED**

I need to know which compartment to use for your **{action.replace('_', ' ').upper()}** operation in the **{service}** service.

**Available Compartments:**
"""

            for i, compartment in enumerate(compartment_data, 1):
                name = compartment.get('name', 'Unknown')
                ocid = compartment.get('id', 'Unknown OCID')
                selection_message += f"{i}. **{name}** (`{ocid}`)\n"

            selection_message += """
**Please select by number or provide compartment details:**
- Type the number (e.g., `1`) to select a compartment
- Or provide: `compartment_id: ocid1.compartment.oc1..your_ocid`
"""

    return {
        "presentation": {
            "summary": selection_message,
            "format": "chat",
            "compartment_selection_required": True,
            "compartment_data": compartment_data,
            "missing_parameters": missing_params,
            "pending_plan": pending_plan
        },
        "compartment_data": compartment_data,  # Store in state for supervisor access
        "next_step": "user_input_required"  # CRITICAL: Signal that we need user input
    }


def _handle_plan_error(state: AgentState, call_llm_func) -> dict:
    """Handle plan errors with user-friendly messages using enhanced error handler."""
    plan_error = state.get("plan_error", "")
    user_query = state.get("user_input", "")

    # Use the fast error handler
    try:
        # Create a mock exception for the plan error
        class PlanError(Exception):
            pass

        error = PlanError(plan_error)
        error_handler = FastErrorHandler()
        call_llm_func = state.get("call_llm", default_call_llm)
        error_response = error_handler.handle_error(
            error, state, "planning", call_llm_func)

        # Get the user-friendly message
        friendly_message = error_response.get(
            'user_message', 'An error occurred while processing your request.')

        # Add specific suggestions based on error type
        if "multiple" in plan_error.lower() or "steps" in plan_error.lower():
            friendly_message += "\n\n**Alternative approaches:**\n• Create one bucket at a time: 'create a bucket named [name]'\n• List existing buckets: 'list buckets'\n• Try a different approach: 'show me my storage resources'"

        elif "unsupported" in plan_error.lower() or "format" in plan_error.lower():
            friendly_message += "\n\n**Try these simpler commands:**\n• For creating resources: 'create a bucket named [name]'\n• For listing resources: 'list [resource type]'\n• For getting help: 'what can you help me with?'"

        elif "planner" in plan_error.lower() or "planning" in plan_error.lower():
            friendly_message += "\n\n**This is a temporary issue our team is working on.**"

        elif "codegen" in plan_error.lower() or "llm" in plan_error.lower():
            friendly_message += "\n\n**Try these alternatives:**\n• Simplify your request: 'create a bucket named test-bucket'\n• Check your OCI credentials are properly configured\n• Try a different type of operation: 'list compartments'"

        elif "keyerror" in plan_error.lower() or "cannot access" in plan_error.lower():
            friendly_message += "\n\n**This is a technical issue our team is working on.**"

        else:
            friendly_message += "\n\n**Try these approaches:**\n• Break down complex requests into simpler ones\n• Make sure you've provided all necessary details\n• Try a different type of operation"

    except Exception as e:
        # Fallback to basic error message
        friendly_message = f"""I encountered an issue processing your request. This can happen when:

• The request is too complex for me to handle
• There's missing information I need
• There are temporary processing issues

Here are some things you can try:
• Break down complex requests into simpler ones
• Make sure you've provided all necessary details
• Try a different type of operation

For example, instead of "create 3 buckets", try "create a bucket named test-bucket".

Would you like to try a different approach?"""

    return {
        "presentation": {
            "summary": friendly_message,
            "format": "chat"
        }
    }
