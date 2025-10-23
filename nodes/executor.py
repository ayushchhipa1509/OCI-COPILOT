# nodes/executor.py
from core.state import AgentState


def executor_node(state: AgentState) -> dict:
    """
    Executes the verified OCI code plan by running the generated Python code.
    The generated code must define a function or return the result (we wrap into a function).
    """
    print("~" * 60)
    print("🚀 EXECUTOR NODE - STARTING")
    print("~" * 60)

    plan = state.get("plan")
    if not plan:
        return {"execution_error": "No plan to execute.", "last_node": "executor"}

    try:
        # Check if this is a multi-step plan
        if 'steps' in plan and isinstance(plan.get('steps'), list):
            return _execute_multi_step_plan(plan, state)

        oci_code = plan.get("oci_code")
        service = plan.get("service")
        if not oci_code:
            return {"execution_error": "No OCI code found in plan.", "last_node": "executor"}

        # verify credentials are present
        oci_creds = state.get("oci_creds") or {}
        print(f"🔍 DEBUG: OCI credentials check:")
        print(f"   - oci_creds keys: {list(oci_creds.keys())}")
        print(f"   - tenancy present: {bool(oci_creds.get('tenancy'))}")
        print(f"   - user present: {bool(oci_creds.get('user'))}")
        print(
            f"   - fingerprint present: {bool(oci_creds.get('fingerprint'))}")
        print(
            f"   - key_content present: {bool(oci_creds.get('key_content'))}")

        if not oci_creds.get("tenancy"):
            return {"execution_error": "Missing tenancy in state['oci_creds'].", "last_node": "executor"}

        print(f"🚀 Executing OCI code for service: {service}")

        # Import required modules for code execution
        from oci_ops.clients import get_client, build_config
        import oci
        from oci.util import to_dict

        # Build proper OCI config from credentials
        oci_config = build_config(oci_creds)

        # Wrapper to support both signatures used by generated code:
        # get_client(service) and get_client(service, state['oci_creds'])
        def _get_client_wrapper(service_name, *args, **kwargs):
            return get_client(service_name, oci_config)

        # Prepare execution environment
        exec_globals = {
            'state': state,
            'get_client': _get_client_wrapper,
            'oci': oci,
            'oci_config': oci_config,
            'plan': plan,  # Add plan to execution context
            'to_dict': to_dict,  # Add to_dict function for OCI object conversion
            # Keep builtins but you might want to restrict in production
            '__builtins__': __builtins__
        }

        # The codegen node returns a body that should "return" a result at the end.
        # Sanitize in case any language hint or code fences slipped through.
        import re
        oci_code_sanitized = str(oci_code)
        if "```" in oci_code_sanitized:
            start = oci_code_sanitized.find("```")
            end = oci_code_sanitized.find("```", start + 3)
            if end > start:
                oci_code_sanitized = oci_code_sanitized[start + 3:end]
        # Remove leading language hint like 'python' + newline
        oci_code_sanitized = re.sub(
            r"^\s*python\s*\r?\n", "", oci_code_sanitized, flags=re.IGNORECASE)

        # QUICK FIX: Remove return statements that cause syntax errors
        oci_code_sanitized = re.sub(
            r'\nreturn\s+results\s*$', '', oci_code_sanitized)
        oci_code_sanitized = re.sub(r'\nreturn\s+.*$', '', oci_code_sanitized)

        # Wrap safely as a function to capture results variable.
        wrapped_code = f'''
def execute_oci_operation():
    results = []  # Initialize results list
{_indent_code(oci_code_sanitized, 4)}
    return results if 'results' in locals() else []

# Execute and capture result
result = execute_oci_operation()
'''
        exec_locals = {}
        exec(wrapped_code, exec_globals, exec_locals)
        result = exec_locals.get('result', [])

        print(f" Execution successful. Final result type: {type(result)}")

        # Normalize result if it is generator or iterator
        if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
            try:
                # convert to list for JSON-serializable structure if possible
                result_list = list(result)
            except Exception:
                result_list = result
        else:
            result_list = result if isinstance(result, list) else [result]

        # CRITICAL: Sanitize results to enforce data contract with PRESENTATION node
        print("🔧 Sanitizing results to ensure dictionary format...")
        sanitized_results = _sanitize_results(result_list)

        print(
            f"✅ Execution successful! Results count: {len(sanitized_results) if isinstance(sanitized_results, list) else 'N/A'}")
        print("~" * 60)
        print("🚀 EXECUTOR NODE - COMPLETED")
        print("~" * 60)
        return {"execution_result": sanitized_results, "last_node": "executor"}

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        error_details = f"Type: {type(e).__name__}, Args: {e.args}, Traceback:\n{tb_str}"
        print(f"❌ Execution failed: {error_details}")

        # Check if it's an OCI ServiceError specifically
        if hasattr(e, 'status') and hasattr(e, 'message'):
            print(
                f"🔍 OCI Service Error Details: Status={e.status}, Message={e.message}")
            return {
                "execution_error": f"OCI API Error (Status {e.status}): {e.message}",
                "last_node": "executor"
            }

        return {"execution_error": str(e), "last_node": "executor"}


def _sanitize_results(results):
    """
    Sanitize execution results to ensure they are in dictionary format for PRESENTATION node.
    This enforces the data contract between EXECUTOR and PRESENTATION nodes.
    """
    if not isinstance(results, list):
        results = [results]

    sanitized = []
    for item in results:
        try:
            # Check if item is an OCI object (has attributes but no keys method)
            if hasattr(item, '__dict__') and not hasattr(item, 'keys'):
                # Convert OCI object to dictionary using oci.util.to_dict
                from oci.util import to_dict
                sanitized_item = to_dict(item)
                print(
                    f"🔧 Converted OCI object {type(item).__name__} to dictionary")
            elif isinstance(item, dict):
                # Already a dictionary, keep as is
                sanitized_item = item
            else:
                # Primitive type or other object, convert to dict representation
                sanitized_item = {
                    'value': str(item),
                    'type': type(item).__name__
                }
                print(
                    f"🔧 Converted {type(item).__name__} to dictionary representation")

            sanitized.append(sanitized_item)

        except Exception as e:
            # Fallback: create error dictionary
            sanitized.append({
                'error': f'Failed to sanitize item: {str(e)}',
                'original_type': type(item).__name__,
                'value': str(item)
            })
            print(f"⚠️ Failed to sanitize item {type(item).__name__}: {e}")

    return sanitized


def _indent_code(code: str, spaces: int) -> str:
    """Helper to indent a multiline code block for function wrapping."""
    prefix = ' ' * spaces
    return '\n'.join(prefix + line if line.strip() != '' else line for line in code.splitlines())


def _execute_multi_step_plan(plan: dict, state: AgentState) -> dict:
    """Execute a multi-step plan by running each step sequentially."""
    print("🔄 Executing multi-step plan...")

    steps = plan.get('steps', [])
    all_results = []
    execution_errors = []

    # Get compartment_id from plan params (applied to all steps)
    compartment_id = plan.get('params', {}).get('compartment_id')

    for i, step in enumerate(steps):
        print(
            f"🔄 Executing step {i+1}/{len(steps)}: {step.get('action', 'unknown')}")

        try:
            # Create a single-step plan for this step
            single_step_plan = {
                'action': step.get('action'),
                'service': step.get('service'),
                'params': step.get('params', {}),
                'oci_code': step.get('oci_code')
            }

            # Add compartment_id to step params if not present
            if compartment_id and 'compartment_id' not in single_step_plan['params']:
                single_step_plan['params']['compartment_id'] = compartment_id

            # Execute this step
            step_result = _execute_single_step(single_step_plan, state)

            if step_result.get('execution_error'):
                execution_errors.append(
                    f"Step {i+1}: {step_result['execution_error']}")
            else:
                all_results.extend(step_result.get('execution_result', []))

        except Exception as e:
            error_msg = f"Step {i+1} failed: {str(e)}"
            execution_errors.append(error_msg)
            print(f"❌ {error_msg}")

    # Return combined results
    if execution_errors:
        return {
            "execution_result": all_results,
            "execution_error": f"Multi-step execution completed with {len(execution_errors)} errors: {'; '.join(execution_errors)}",
            "last_node": "executor"
        }
    else:
        return {
            "execution_result": all_results,
            "last_node": "executor"
        }


def _execute_single_step(step_plan: dict, state: AgentState) -> dict:
    """Execute a single step from a multi-step plan."""
    # This is a simplified version of the main executor logic
    # for executing individual steps

    oci_code = step_plan.get("oci_code")
    if not oci_code:
        return {"execution_error": "No OCI code found in step."}

    # verify credentials are present
    oci_creds = state.get("oci_creds") or {}
    if not oci_creds.get("tenancy"):
        return {"execution_error": "Missing tenancy in state['oci_creds']."}

    try:
        # Import required modules for code execution
        from oci_ops.clients import get_client, build_config
        import oci

        # Build proper OCI config from credentials
        oci_config = build_config(oci_creds)

        # Wrapper to support both signatures used by generated code
        def _get_client_wrapper(service_name, *args, **kwargs):
            return get_client(service_name, oci_config)

        # Prepare execution environment
        exec_globals = {
            'state': state,
            'get_client': _get_client_wrapper,
            'oci': oci,
            'oci_config': oci_config,
            'plan': step_plan,
            '__builtins__': __builtins__
        }

        # Sanitize code
        import re
        oci_code_sanitized = str(oci_code)
        if "```" in oci_code_sanitized:
            start = oci_code_sanitized.find("```")
            end = oci_code_sanitized.find("```", start + 3)
            if end > start:
                oci_code_sanitized = oci_code_sanitized[start + 3:end]

        oci_code_sanitized = re.sub(
            r"^\s*python\s*\r?\n", "", oci_code_sanitized, flags=re.IGNORECASE)
        oci_code_sanitized = re.sub(
            r'\nreturn\s+results\s*$', '', oci_code_sanitized)
        oci_code_sanitized = re.sub(r'\nreturn\s+.*$', '', oci_code_sanitized)

        # Wrap safely as a function
        wrapped_code = f'''
def execute_oci_operation():
{_indent_code(oci_code_sanitized, 4)}
    return results if 'results' in locals() else []

# Execute and capture result
result = execute_oci_operation()
'''
        exec_locals = {}
        exec(wrapped_code, exec_globals, exec_locals)
        result = exec_locals.get('result', [])

        # Normalize result
        if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
            try:
                result_list = list(result)
            except Exception:
                result_list = result
        else:
            result_list = result if isinstance(result, list) else [result]

        # Sanitize results
        sanitized_results = _sanitize_results(result_list)

        return {
            "execution_result": sanitized_results,
            "last_node": "executor"
        }

    except Exception as e:
        return {"execution_error": f"Step execution failed: {str(e)}"}
