# nodes/presentation_node.py
from core.state import AgentState
from core.prompts import load_prompt
from core.llm_manager import call_llm as default_call_llm
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

    # Handle safety confirmation prompts
    if state.get("confirmation_required"):
        return _handle_safety_confirmation(state)

    # Handle action cancellation
    if state.get("action_cancelled"):
        return _handle_action_cancellation(state)

    # Handle parameter gathering
    if state.get("parameter_gathering_required"):
        return _handle_parameter_gathering(state)

    # Handle compartment listing for parameter selection
    if state.get("compartment_listing_complete"):
        return _handle_compartment_selection(state)

    data_source = state.get("data_source", "live_api")
    user_query = state.get("user_input", "")
    execution_result = state.get("execution_result", {})
    call_llm_func = state.get("call_llm", default_call_llm)

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
                normalized_execution_result = execution_result or {"data": []}

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


def _parse_parameter_response(user_input: str, missing_params: list, compartment_data: list = None) -> dict:
    """Parse user input to extract parameter values."""
    selected_params = {}

    # Check if user selected a number for compartment
    if compartment_data and user_input.strip().isdigit():
        selection_num = int(user_input.strip())
        if 1 <= selection_num <= len(compartment_data):
            selected_compartment = compartment_data[selection_num - 1]
            selected_params['compartment_id'] = selected_compartment.get('id')
            print(
                f"🔄 User selected compartment #{selection_num}: {selected_compartment.get('name')}")
            return selected_params

    # Simple parsing: look for "param_name: value" patterns
    lines = user_input.split('\n')
    for line in lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key in missing_params:
                selected_params[key] = value

    return selected_params


def _handle_parameter_gathering(state: AgentState) -> dict:
    """Handle parameter gathering for deployment operations."""
    pending_plan = state.get("pending_plan", {})
    missing_params = state.get("missing_parameters", [])
    action = pending_plan.get("action", "unknown action")
    service = pending_plan.get("service", "unknown service")

    # Build parameter gathering message
    gathering_message = f"""
🔧 **PARAMETER GATHERING REQUIRED**

I need additional information to complete your **{action.replace('_', ' ').upper()}** operation in the **{service}** service.

**Missing Parameters:**
{', '.join(missing_params)}

Please provide the missing information:
"""

    # Add specific guidance based on missing parameters
    if "compartment_id" in missing_params:
        gathering_message += """
**For Compartment Selection:**
Please provide the compartment OCID where you want to create the resource.
You can find compartment OCIDs by running: "list compartments"
"""

    if "shape" in missing_params:
        gathering_message += """
**For Instance Shape:**
Please provide the shape name (e.g., "VM.Standard.E2.1.Micro").
You can find available shapes by running: "list shapes"
"""

    if "image_id" in missing_params:
        gathering_message += """
**For Instance Image:**
Please provide the image OCID (e.g., "ocid1.image.oc1...").
You can find available images by running: "list images"
"""

    if "subnet_id" in missing_params:
        gathering_message += """
**For Subnet Selection:**
Please provide the subnet OCID where you want to create the resource.
You can find subnet OCIDs by running: "list subnets"
"""

    gathering_message += """
**Example Response:**
compartment_id: ocid1.compartment.oc1..your_compartment_ocid
shape: VM.Standard.E2.1.Micro
image_id: ocid1.image.oc1..your_image_ocid
"""

    return {
        "presentation": {
            "summary": gathering_message,
            "format": "chat",
            "parameter_gathering_required": True,
            "missing_parameters": missing_params,
            "pending_plan": pending_plan
        }
    }


def _handle_compartment_selection(state: AgentState) -> dict:
    """Handle compartment selection with numbered list."""
    pending_plan = state.get("pending_plan", {})
    missing_params = state.get("missing_parameters", [])
    action = pending_plan.get("action", "unknown action")
    service = pending_plan.get("service", "unknown service")

    # Get the execution result (compartment list)
    execution_result = state.get("execution_result", {})
    compartment_data = execution_result.get("data", [])

    if not compartment_data:
        # Fallback if no compartments found
        selection_message = f"""
🔧 **COMPARTMENT SELECTION REQUIRED**

I need to know which compartment to use for your **{action.replace('_', ' ').upper()}** operation in the **{service}** service.

Unfortunately, I couldn't retrieve the list of compartments. Please provide the compartment OCID manually:

**Example Response:**
compartment_id: ocid1.compartment.oc1..your_compartment_ocid
"""
    else:
        # Create numbered list of compartments
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
        "compartment_data": compartment_data  # Store in state for supervisor access
    }
