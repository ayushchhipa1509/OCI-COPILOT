# nodes/codegen_node.py
import json
import re
import os
from core.state import AgentState
from core.llm_manager import call_llm as default_call_llm
from core.fast_error_handler import handle_node_error


def load_codegen_prompt(service="unknown") -> str:
    """Load the codegen prompt from the prompts folder with service-specific patterns."""
    base_prompt_path = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "prompts", "codegen", "base.md")

    service_prompt_path = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "prompts", "codegen", f"{service}.md")

    # Load base prompt
    try:
        with open(base_prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        base_prompt = """You are an expert OCI Python SDK code generator. 
Generate Python code using get_client() for OCI operations.
Use attribute access, handle pagination, return results list."""

    # Load service-specific prompt
    service_prompt = ""
    if service != "unknown":
        try:
            with open(service_prompt_path, "r", encoding="utf-8") as f:
                service_prompt = f.read()
        except FileNotFoundError:
            print(f"⚠️ Service-specific prompt not found for: {service}")
            service_prompt = ""

    # Combine base and service prompts
    if service_prompt:
        return f"{base_prompt}\n\n{service_prompt}"
    else:
        return base_prompt


def get_codegen_prompt(plan, action, params, user_query="", is_multi_step=False, service="unknown"):
    """Generate intelligent codegen prompt using the prompts folder with service-specific patterns."""

    # Load service-specific prompt from files
    base_prompt = load_codegen_prompt(service)

    # Add multi-step specific instructions
    multi_step_instructions = ""
    if is_multi_step:
        multi_step_instructions = """

## Multi-Step Query Instructions:
This is a MULTI_STEP_REQUIRED query that needs multiple API calls and intelligent filtering.

### Key Requirements:
1. **Fetch primary resources first** (e.g., list_instances)
2. **Make additional API calls** for related data (e.g., list_vnic_attachments, get_vnic)
3. **Apply intelligent filtering** based on user query
4. **Extract specific requested data** (e.g., public IPs, security rules)
5. **Only return resources that match the criteria**

### Example for "instances with public IP":
```python
# Step 1: List all instances
instances_response = compute_client.list_instances(compartment_id=compartment_id)
results.extend(instances_response.data)

# Step 2: For each instance, check for public IP
enhanced_results = []
for instance in results:
    try:
        vnic_attachments = compute_client.list_vnic_attachments(
            compartment_id=instance.compartment_id,
            instance_id=instance.id
        )
        
        public_ips = []
        for vnic_attachment in vnic_attachments.data:
            vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
            if vnic.public_ip:
                public_ips.append(vnic.public_ip)
        
        if public_ips:
            instance.public_ips = public_ips
            instance.has_public_ip = True
            enhanced_results.append(instance)
    except Exception:
        continue

results = enhanced_results
```"""

    # Add the specific plan context
    prompt_with_plan = f"""{base_prompt}{multi_step_instructions}

## Current Task:
Convert this planner output into executable Python code:

```json
{json.dumps(plan, indent=2)}
```

## User Query Context:
User Query: "{user_query}"

Generate clean, production-ready Python code that accomplishes this OCI operation.
IMPORTANT: 
1. Do NOT include 'return' statements. Just set the 'results' variable and let the executor handle the return.
2. Do NOT reference 'params' variable directly. Use hardcoded values from the plan parameters.
3. All variables like oci_config, state, get_client are available in the execution context.
4. Use the user_query variable to apply intelligent filtering (e.g., public IP queries, state filtering).
5. For public IP queries, fetch VNIC attachments and extract public IP information.
6. For state-based queries (running/stopped), filter results by lifecycle_state.
7. For security list queries with specific rules, filter by rule content."""

    return prompt_with_plan


def codegen_node(state: AgentState) -> dict:
    """
    LLM-powered code generator:
    Takes the planner's plan (action + params) and asks the LLM to generate executable
    OCI SDK Python code. The code should:
      - Use get_client('<service>', state['oci_creds']) to create OCI clients
      - Traverse tenancy root + all compartments if 'all_compartments' is requested
      - Return aggregated results in a list
    Produces a plan enriched with 'oci_code', 'service', and 'safety_tier'.
    """
    print("+" * 60)
    print("⚙️ CODEGEN NODE - STARTING")
    print("+" * 60)

    plan = state.get("plan")
    call_llm_func = state.get("call_llm", default_call_llm)

    print(f"🔍 DEBUG: Plan received in codegen:")
    print(f"   - Plan keys: {list(plan.keys()) if plan else 'None'}")
    print(f"   - Action: {plan.get('action') if plan else 'None'}")
    print(f"   - Service: {plan.get('service') if plan else 'None'}")
    print(f"   - Params: {plan.get('params') if plan else 'None'}")

    if not plan:
        return {"plan": None, "plan_error": "No plan provided to codegen_node.", "last_node": "codegen"}

    # If already contains code, just return
    if isinstance(plan, dict) and plan.get("oci_code"):
        return {"plan": plan, "last_node": "codegen"}

    # Extract action + params
    action = None
    params = {}
    if "action" in plan:
        action = plan["action"]
        params = plan.get("params", {}) or {}
    elif "steps" in plan and isinstance(plan["steps"], list) and len(plan["steps"]) > 0:
        # For multi-step plans, we need to generate code for each step
        return _handle_multi_step_codegen(plan, state, call_llm_func)
    else:
        return {"plan": None, "plan_error": "Unsupported plan format for code generation.", "last_node": "codegen"}

    # Enforce desired default: list_* actions should search all compartments by default
    if isinstance(params, dict) and isinstance(action, str) and action.lower().startswith("list_"):
        if not params.get("all_compartments", False):
            params["all_compartments"] = True

    # Get user query for intelligent filtering
    user_query = state.get("user_input", "") or state.get(
        "normalized_query", "")

    # Check if this is a multi-step query
    execution_strategy = state.get("execution_strategy", "unknown")
    is_multi_step = execution_strategy == "multi_step"

    # Check if this is a retry with error feedback
    feedback = state.get("feedback", "")
    error_context = state.get("error_context", "")

    # Determine service from action or plan
    service = plan.get("service", "unknown")
    if service == "unknown":
        # Fallback service mapping
        service_map = {
            "list_instances": "compute",
            "get_instance": "compute",
            "start_instance": "compute",
            "stop_instance": "compute",
            "terminate_instance": "compute",
            "list_volumes": "blockstorage",
            "list_buckets": "objectstorage",
            "list_compartments": "identity",
            "list_users": "identity",
            "list_groups": "identity",
            "list_vcns": "virtualnetwork",
            "list_subnets": "virtualnetwork",
            "list_alarms": "monitoring",
            "list_databases": "database",
            "list_load_balancers": "loadbalancer"
        }
        service = service_map.get(action, "unknown")

    # Load comprehensive codegen prompt with service-specific patterns
    print(f"🎯 Loading service-specific prompt for: {service}")
    codegen_prompt = get_codegen_prompt(
        plan, action, params, user_query, is_multi_step, service)

    # Add error context if this is a retry
    if feedback and error_context:
        if error_context == "syntax_error":
            codegen_prompt += f"\n\n## CORRECTION REQUEST - SYNTAX ERROR\nYour previous code failed static verification. Please fix the syntax/structure issues:\n{feedback}"
        elif error_context == "runtime_error":
            codegen_prompt += f"\n\n## CORRECTION REQUEST - RUNTIME ERROR\nYour previous code failed during execution. Please analyze the error and fix the logic:\n{feedback}"

    messages = [
        {"role": "system", "content": codegen_prompt},
        {"role": "user", "content": f"Generate OCI code for action '{action}' with params {params}. User wants: {user_query}"}
    ]

    llm_output = call_llm_func(state, messages, 'codegen')

    try:
        print(f"🔍 Raw Codegen Response: {llm_output}")
        response_str = str(llm_output).strip()

        # Service already determined above

        # Extract Python code block if fenced
        if "```" in response_str:
            code_start = response_str.find("```")
            code_end = response_str.find("```", code_start + 3)
            if code_end > code_start:
                oci_code = response_str[code_start + 3:code_end]
                # Remove optional language hint like "python" with flexible whitespace and CRLF
                # Handles cases like: "python\n", " python \r\n", etc.
                oci_code = re.sub(r"^\s*python\s*\r?\n", "",
                                  oci_code, flags=re.IGNORECASE).strip()
            else:
                oci_code = response_str
        else:
            # Also handle non-fenced answers that may start with a language hint
            oci_code = re.sub(r"^\s*python\s*\r?\n", "",
                              response_str, flags=re.IGNORECASE).strip()

        # Normalize common misnamings in service identifiers within the generated code
        # so they align with oci_ops.clients.ALLOWED_CLIENTS keys.
        def _normalize_service_names_in_code(code: str) -> str:
            patterns = [
                (r"get_client\(\s*['\"]core['\"]\s*,",
                 "get_client('compute',"),
                (r"get_client\(\s*['\"]block_storage['\"]\s*,",
                 "get_client('blockstorage',"),
                (r"get_client\(\s*['\"]virtual_network['\"]\s*,",
                 "get_client('virtualnetwork',"),
                (r"get_client\(\s*['\"]object_storage['\"]\s*,",
                 "get_client('objectstorage',"),
                (r"get_client\(\s*['\"]load_balancer['\"]\s*,",
                 "get_client('loadbalancer',"),
            ]
            for pat, repl in patterns:
                code = re.sub(pat, repl, code)
            return code

        oci_code = _normalize_service_names_in_code(oci_code)

        # Remove invalid kwarg 'include_root' from list_compartments calls (not supported by OCI SDK)
        try:
            oci_code = re.sub(r"(list_compartments\([^)]+),\s*include_root\s*=\s*True(\s*[,)])",
                              r"\1\2", oci_code)
            oci_code = re.sub(r"include_root\s*=\s*True\s*,\s*", "", oci_code)
            oci_code = re.sub(r"\s*,\s*include_root\s*=\s*True", "", oci_code)
        except Exception:
            pass

        # Fix compartment object access - change dictionary access to attribute access
        try:
            # Fix compartment['id'] -> compartment.id
            oci_code = re.sub(
                r"compartment\[['\"](id|name|lifecycle_state)['\"]\]", r"compartment.\1", oci_code)
            # Fix any other object attribute access patterns
            oci_code = re.sub(
                r"(\w+)\[['\"](id|name|lifecycle_state|display_name)['\"]\]", r"\1.\2", oci_code)
        except Exception:
            pass

        # Resolve template variables in the generated code
        try:
            # Replace ${config['compartment_id']} with actual tenancy ID access
            oci_code = re.sub(
                r"\$\{config\[['\"']compartment_id['\"']\]\}", "oci_config['tenancy']", oci_code)
            # Also handle direct compartment_id template resolution in params
            if isinstance(params, dict) and params.get("compartment_id") == "${config['compartment_id']}":
                # This will be resolved at runtime to use tenancy ID
                pass
        except Exception:
            pass

        # Fix common function call issues
        try:
            # Replace get_oci_config() with oci_config (which is available in execution context)
            oci_code = re.sub(r"get_oci_config\(\)", "oci_config", oci_code)
            # Replace get_client calls to use the correct function signature
            oci_code = re.sub(
                r"get_client\(['\"]([^'\"]+)['\"],\s*oci_config\)", r"get_client('\1', oci_config)", oci_code)
        except Exception:
            pass

        # If action targets Object Storage buckets but code lacks namespace_name, inject it.
        is_objectstorage = (service == 'objectstorage') or (
            isinstance(action, str) and 'bucket' in action.lower())
        if is_objectstorage:
            # Create a namespace resolver prelude
            namespace_prelude = (
                "namespace = None\n"
                "try:\n"
                "    namespace = state.get('oci_creds', {}).get('namespace')\n"
                "except Exception:\n"
                "    namespace = None\n"
                "if not namespace:\n"
                "    _os_client_for_ns = get_client('objectstorage', state['oci_creds'])\n"
                "    _ns_resp = _os_client_for_ns.get_namespace()\n"
                "    namespace = getattr(_ns_resp, 'data', _ns_resp)\n"
            )
            # Ensure list_buckets include namespace_name parameter when missing
            # Add namespace prelude at the top and rewrite calls lacking namespace_name=
            if 'list_buckets' in oci_code and 'namespace_name' not in oci_code:
                oci_code = namespace_prelude + "\n" + oci_code
                # Replace occurrences like client.list_buckets(<args...>) inserting namespace_name first
                try:
                    oci_code = re.sub(
                        r"(\.list_buckets\()\s*",
                        r"\\1namespace_name=namespace, ",
                        oci_code
                    )
                except Exception:
                    pass

        # Ensure code defines a results list (but NO return statement)
        code_stripped = oci_code.strip()
        if 'results' not in code_stripped:
            oci_code = "results = []\n" + oci_code

        # REMOVE any return statements that may have been generated
        oci_code = re.sub(r'\nreturn\s+.*$', '', oci_code, flags=re.MULTILINE)
        oci_code = re.sub(r'^return\s+.*\n?', '', oci_code, flags=re.MULTILINE)

        # REMOVE any params references and replace with actual values
        if isinstance(params, dict):
            # Replace params.get('all_compartments', False) with actual boolean value
            all_compartments = params.get('all_compartments', False)
            oci_code = re.sub(
                r"params\.get\(['\"]all_compartments['\"],\s*False\)", str(all_compartments), oci_code)
            oci_code = re.sub(
                r"params\.get\(['\"]all_compartments['\"],\s*True\)", str(all_compartments), oci_code)
            oci_code = re.sub(
                r"params\.get\(['\"]all_compartments['\"].*?\)", str(all_compartments), oci_code)

            # Replace other common params references
            for key, value in params.items():
                if isinstance(value, str):
                    oci_code = re.sub(
                        f"params\\.get\\(['\"]({key})['\"].*?\\)", f"'{value}'", oci_code)
                else:
                    oci_code = re.sub(
                        f"params\\.get\\(['\"]({key})['\"].*?\\)", str(value), oci_code)

        # Safety tier default: safe for listing/getting, destructive otherwise
        safety_tier = "safe"
        destructive_verbs = ["delete", "terminate", "detach", "stop"]
        if any(verb in (action or "").lower() for verb in destructive_verbs):
            safety_tier = "destructive"

        updated_plan = plan.copy() if isinstance(plan, dict) else {
            "action": action, "params": params}
        # Keep the enforced params in the updated plan
        if isinstance(updated_plan, dict):
            if "params" not in updated_plan or not isinstance(updated_plan["params"], dict):
                updated_plan["params"] = {}
            updated_plan["params"].update(params or {})
        updated_plan.update({
            "oci_code": oci_code,
            "service": service,
            "safety_tier": safety_tier,
            "generated_by": "codegen_node"
        })

        print(f"✅ Generated OCI code for service: {service}")
        print(f"🔒 Safety tier: {safety_tier}")
        print("+" * 60)
        print("⚙️ CODEGEN NODE - COMPLETED")
        print("+" * 60)

        # DEBUG: Log generated code for delete operations
        if action and 'delete' in action.lower():
            print(f"🔍 DEBUG: Generated code for {action}:")
            print(f"```python\n{oci_code}\n```")

        return {"plan": updated_plan, "last_node": "codegen"}
    except Exception as e:
        # Use fast LLM error handler
        error_response = handle_node_error(e, state, "codegen", call_llm_func)

        # Fall back to a minimal plan to avoid breaking the chain
        fallback_plan = {"action": action or "unknown_action", "params": params or {}, "service": (
            action and action.split('_')[1]) if isinstance(action, str) else "unknown"}
        return {"plan": fallback_plan, "plan_error": error_response['user_message'], "last_node": "codegen"}


def _handle_multi_step_codegen(plan: dict, state: AgentState, call_llm_func) -> dict:
    """Handle code generation for multi-step plans with optimization for similar actions."""
    print("🔄 Generating code for multi-step plan...")

    steps = plan.get('steps', [])

    # Check if all steps are similar actions (optimization opportunity)
    if _are_steps_similar(steps):
        print("🚀 Optimizing: All steps are similar actions, generating efficient batch code...")
        return _generate_optimized_batch_code(steps, state, call_llm_func)
    else:
        print("🔄 Generating individual code for each step...")
        return _generate_individual_step_code(steps, state, call_llm_func)


def _are_steps_similar(steps: list) -> bool:
    """Check if all steps are similar actions that can be optimized."""
    if len(steps) < 2:
        return False

    # Get the first step as reference
    first_action = steps[0].get('action')
    first_service = steps[0].get('service')

    # Check if all steps have the same action and service
    for step in steps[1:]:
        if step.get('action') != first_action or step.get('service') != first_service:
            return False

    # Check if it's a batchable action (create, delete, etc.)
    batchable_actions = ['create_bucket', 'delete_bucket',
                         'create_volume', 'create_instance']
    return first_action in batchable_actions


def _generate_optimized_batch_code(steps: list, state: AgentState, call_llm_func) -> dict:
    """Generate optimized batch code for similar actions."""
    first_step = steps[0]
    action = first_step.get('action')
    service = first_step.get('service')

    # Extract all the resource names/parameters
    resource_names = []
    for step in steps:
        params = step.get('params', {})
        if 'name' in params:
            resource_names.append(params['name'])
        elif 'bucket_name' in params:
            resource_names.append(params['bucket_name'])
        elif 'display_name' in params:
            resource_names.append(params['display_name'])

    # Create optimized prompt for batch operations
    user_query = state.get("user_input", "")

    if action == 'create_bucket':
        optimized_prompt = f"""
Generate optimized OCI code to create multiple buckets in a single operation.

Action: {action}
Service: {service}
Resource Names: {resource_names}
Compartment ID: {first_step.get('params', {}).get('compartment_id', 'PLACEHOLDER')}

CRITICAL REQUIREMENTS - Follow this EXACT pattern:
1. Use get_client('objectstorage', oci_config) to create the client
2. Get namespace with: namespace = objectstorage_client.get_namespace().data
3. Use correct create_bucket syntax: objectstorage_client.create_bucket(namespace_name=namespace, create_bucket_details=create_bucket_details)
4. Create CreateBucketDetails object with: oci.object_storage.models.CreateBucketDetails(name=bucket_name, compartment_id=compartment_id)

EXAMPLE CORRECT PATTERN:
```python
objectstorage_client = get_client('objectstorage', oci_config)
namespace = objectstorage_client.get_namespace().data

for bucket_name in bucket_names:
    create_bucket_details = oci.object_storage.models.CreateBucketDetails(
        name=bucket_name,
        compartment_id=compartment_id
    )
    response = objectstorage_client.create_bucket(
        namespace_name=namespace,
        create_bucket_details=create_bucket_details
    )
```

Generate efficient code that:
1. Creates all buckets in a single loop
2. Handles errors for each bucket individually
3. Returns results for all buckets
4. Uses the same compartment_id for all buckets
5. Follows the EXACT OCI SDK pattern above

Return ONLY the Python code, no explanations.
"""
    else:
        # Fallback to individual generation for other actions
        return _generate_individual_step_code(steps, state, call_llm_func)

    messages = [
        {"role": "system", "content": optimized_prompt},
        {"role": "user",
            "content": f"Generate optimized batch code for {len(resource_names)} {action} operations"}
    ]

    try:
        llm_output = call_llm_func(state, messages, 'codegen')
        response_str = str(llm_output).strip()

        # Extract code from response
        if "```" in response_str:
            code_start = response_str.find("```")
            code_end = response_str.find("```", code_start + 3)
            if code_end > code_start:
                oci_code = response_str[code_start + 3:code_end]
                oci_code = re.sub(r"^\s*python\s*\r?\n", "",
                                  oci_code, flags=re.IGNORECASE).strip()
            else:
                oci_code = response_str
        else:
            oci_code = re.sub(r"^\s*python\s*\r?\n", "",
                              response_str, flags=re.IGNORECASE).strip()

        # Create optimized plan with single batch code
        optimized_plan = {
            'action': f'batch_{action}',
            'service': service,
            'params': first_step.get('params', {}),
            'oci_code': oci_code,
            'optimized': True,
            'batch_size': len(steps)
        }

        print(
            f"✅ Generated optimized batch code for {len(steps)} {action} operations")
        return {"plan": optimized_plan, "last_node": "codegen"}

    except Exception as e:
        print(
            f"⚠️ Batch optimization failed, falling back to individual generation: {e}")

        # Use fast LLM error handler for logging
        error_response = handle_node_error(
            e, state, "codegen_batch", call_llm_func)

        return _generate_individual_step_code(steps, state, call_llm_func)


def _generate_individual_step_code(steps: list, state: AgentState, call_llm_func) -> dict:
    """Generate individual code for each step (original behavior)."""
    updated_steps = []

    for i, step in enumerate(steps):
        print(
            f"🔄 Generating code for step {i+1}/{len(steps)}: {step.get('action', 'unknown')}")

        # Create a single-step plan for code generation
        single_step_plan = {
            'action': step.get('action'),
            'service': step.get('service'),
            'params': step.get('params', {})
        }

        # Generate code for this step
        step_result = _generate_single_step_code(
            single_step_plan, state, call_llm_func)

        if step_result.get('plan_error'):
            return {"plan": None, "plan_error": f"Step {i+1} codegen failed: {step_result['plan_error']}", "last_node": "codegen"}

        # Add the generated code to the step
        updated_step = step.copy()
        updated_step['oci_code'] = step_result['plan'].get('oci_code')
        updated_steps.append(updated_step)

    # Update the plan with generated code for all steps
    updated_plan = {
        'steps': updated_steps,
        'requires_confirmation': True,
        'safety_tier': 'destructive'
    }

    print(f"✅ Generated code for {len(updated_steps)} steps")
    return {"plan": updated_plan, "last_node": "codegen"}


def _generate_single_step_code(step_plan: dict, state: AgentState, call_llm_func) -> dict:
    """Generate code for a single step in a multi-step plan."""
    action = step_plan.get('action')
    params = step_plan.get('params', {})
    service = step_plan.get('service', 'unknown')

    # Get user query for context
    user_query = state.get("user_input", "") or state.get(
        "normalized_query", "")

    # Determine service from action if not provided
    if service == "unknown":
        service_map = {
            "list_instances": "compute",
            "get_instance": "compute",
            "start_instance": "compute",
            "stop_instance": "compute",
            "terminate_instance": "compute",
            "list_volumes": "blockstorage",
            "list_buckets": "objectstorage",
            "create_bucket": "objectstorage",
            "delete_bucket": "objectstorage",
            "list_compartments": "identity",
            "list_users": "identity",
            "list_groups": "identity",
            "list_vcns": "virtualnetwork",
            "list_subnets": "virtualnetwork",
            "list_alarms": "monitoring",
            "list_databases": "database",
            "list_load_balancers": "loadbalancer"
        }
        service = service_map.get(action, "unknown")

    # Load codegen prompt
    codegen_prompt = get_codegen_prompt(
        step_plan, action, params, user_query, False, service)

    messages = [
        {"role": "system", "content": codegen_prompt},
        {"role": "user", "content": f"Generate OCI code for action '{action}' with params {params}. User wants: {user_query}"}
    ]

    try:
        llm_output = call_llm_func(state, messages, 'codegen')
        response_str = str(llm_output).strip()

        # Extract code from response
        if "```python" in response_str:
            start = response_str.find("```python") + 10
            end = response_str.find("```", start)
            if end > start:
                oci_code = response_str[start:end].strip()
            else:
                oci_code = response_str[start:].strip()
        elif "```" in response_str:
            start = response_str.find("```") + 3
            end = response_str.find("```", start)
            if end > start:
                oci_code = response_str[start:end].strip()
            else:
                oci_code = response_str[start:].strip()
        else:
            oci_code = response_str

        # Create updated plan with generated code
        updated_plan = step_plan.copy()
        updated_plan['oci_code'] = oci_code

        return {"plan": updated_plan}

    except Exception as e:
        # Use fast LLM error handler
        error_response = handle_node_error(
            e, state, "codegen_individual", call_llm_func)
        return {"plan": None, "plan_error": error_response['user_message']}
