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
        oci_code = plan.get("oci_code")
        service = plan.get("service")
        if not oci_code:
            return {"execution_error": "No OCI code found in plan.", "last_node": "executor"}

        # verify credentials are present
        oci_creds = state.get("oci_creds") or {}
        if not oci_creds.get("tenancy"):
            return {"execution_error": "Missing tenancy in state['oci_creds'].", "last_node": "executor"}

        print(f" Executing OCI code for service: {service}")

        # Import required modules for code execution
        from oci_ops.clients import get_client, build_config
        import oci

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
        print(f" Execution failed: {e}")
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
