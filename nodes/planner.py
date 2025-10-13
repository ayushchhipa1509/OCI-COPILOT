# nodes/planner.py
import json
import time
from core.state import AgentState
from core.llm_manager import call_llm as default_call_llm
from core.prompts import load_prompt
from core.enhanced_intent_analyzer import analyze_intent_and_classify
from core.query_templates import get_template_plan


def planner_node(state: AgentState) -> dict:
    """
    Enhanced planner with query classification and optimized execution strategy.
    """
    start_time = time.time()
    print("*" * 60)
    print("⚙️ ENHANCED PLANNER NODE - STARTING")
    print("*" * 60)

    normalized_query = state.get(
        "normalized_query", "") or state.get("user_input", "")
    call_llm_func = state.get("call_llm", default_call_llm)

    # Debug logging
    print(f"DEBUG: call_llm_func from state: {call_llm_func}")
    print(f"DEBUG: default_call_llm: {default_call_llm}")
    print(f"DEBUG: call_llm_func is None: {call_llm_func is None}")

    # Safety check for call_llm_func
    if call_llm_func is None:
        print("⚠️ WARNING: call_llm_func is None, using default_call_llm")
        call_llm_func = default_call_llm

    # Step 1: Unified analysis (intent + classification in one step)
    print(f"🔍 Step 1: Unified analysis (intent + classification)...")
    analysis_start = time.time()
    analysis_result = analyze_intent_and_classify(normalized_query, state)
    analysis_time = time.time() - analysis_start
    print(f"✅ Unified analysis completed in {analysis_time:.2f}s")
    print(f"   Resource: {analysis_result.get('primary_resource')}")
    print(f"   Action: {analysis_result.get('action')}")
    print(f"   Execution Type: {analysis_result.get('execution_type')}")
    print(f"   Confidence: {analysis_result.get('confidence')}")
    print(f"   Method: {analysis_result.get('analysis_method')}")

    # Step 2: Route based on execution type
    execution_type = analysis_result.get('execution_type')

    if execution_type == "DIRECT_FETCH":
        print(f"\n⚡ Step 2: Using DIRECT_FETCH strategy...")
        return _handle_direct_fetch(analysis_result, state, call_llm_func, start_time)
    elif execution_type == "MULTI_STEP_REQUIRED":
        print(f"\n🔧 Step 2: Using MULTI_STEP strategy...")
        return _handle_multi_step(normalized_query, analysis_result, state, call_llm_func, start_time)
    else:
        print(f"\n🤖 Step 2: Using LLM fallback strategy...")
        return _handle_llm_fallback(normalized_query, analysis_result, state, call_llm_func, start_time)


def _handle_direct_fetch(analysis_result: dict, state: dict, call_llm_func, start_time: float) -> dict:
    """Handle DIRECT_FETCH queries with template-based planning."""
    print(f"📋 Checking for direct fetch template...")
    template_start = time.time()
    template_plan = get_template_plan(analysis_result)
    template_time = time.time() - template_start

    if template_plan:
        print(f"✅ Template found in {template_time:.3f}s!")
        print(f"   Type: {template_plan.get('type')}")
        plan = _convert_template_to_plan(template_plan, analysis_result)
        plan = _enforce_all_compartments(plan)

        # Apply safety flags
        plan = _apply_safety_flags(plan, analysis_result)

        total_time = time.time() - start_time
        print(f"✅ Plan generated in {total_time:.2f}s (template only)")
        print("*" * 60)
        return {
            "plan": plan,
            "last_node": "planner",
            "planning_time": total_time,
            "execution_strategy": "direct_fetch"
        }
    else:
        print(f"⚠️ No template found, falling back to LLM")
        return _handle_llm_fallback("", analysis_result, state, call_llm_func, start_time)


def _handle_multi_step(normalized_query: str, analysis_result: dict, state: dict, call_llm_func, start_time: float) -> dict:
    """Handle MULTI_STEP_REQUIRED queries with LLM planning."""
    print(f"🤖 Using LLM for multi-step planning...")
    llm_start = time.time()

    # Use enhanced prompt with intent context
    try:
        planner_prompt = load_prompt('planner_enhanced')
    except:
        print("⚠️ Enhanced prompt not found, using standard planner")
        planner_prompt = load_prompt('planner')

    # Fill in the prompt template with analysis context
    planner_prompt = planner_prompt.replace(
        '{intent}', json.dumps(analysis_result, indent=2))
    planner_prompt = planner_prompt.replace('{query}', normalized_query)
    planner_prompt = planner_prompt.replace(
        '{classification}', json.dumps(analysis_result, indent=2))

    messages = [
        {'role': 'system', 'content': planner_prompt},
        {'role': 'user', 'content': f"Generate multi-step plan for: {normalized_query}"}
    ]

    try:
        # Use Pro model for complex multi-step planning
        print("🧠 Using Pro model for complex multi-step planning")
        # Use codegen node config (Pro model) for complex reasoning
        llm_output = call_llm_func(state, messages, 'codegen')
        llm_time = time.time() - llm_start
        print(f"✅ LLM planning completed in {llm_time:.2f}s")

        response_str = str(llm_output).strip()
        plan = json.loads(response_str)
        plan = _enforce_all_compartments(plan)

        # Apply safety flags
        plan = _apply_safety_flags(plan, analysis_result)

        total_time = time.time() - start_time

        print(f"✅ Generated multi-step plan")
        print(f"⏱️ Total planning time: {total_time:.2f}s")
        print("*" * 60)

        return {
            "plan": plan,
            "last_node": "planner",
            "planning_time": total_time,
            "execution_strategy": "multi_step",
            "analysis_result": analysis_result
        }

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Multi-step planning error: {e}")

        # Check for specific error types
        if "ResourceExhausted" in error_msg or "429" in error_msg:
            print("⚠️ Rate limit exceeded, trying fallback model...")
            # Try with fallback model (Groq)
            try:
                # Use normalizer config (Groq fallback)
                llm_output = call_llm_func(state, messages, 'normalizer')
                llm_time = time.time() - llm_start
                print(f"✅ Fallback planning completed in {llm_time:.2f}s")

                response_str = str(llm_output).strip()
                plan = json.loads(response_str)
                plan = _enforce_all_compartments(plan)
                plan = _apply_safety_flags(plan, analysis_result)

                total_time = time.time() - start_time
                print(f"✅ Generated fallback plan")
                print(f"⏱️ Total planning time: {total_time:.2f}s")

                return {
                    "plan": plan,
                    "last_node": "planner",
                    "planning_time": total_time,
                    "execution_strategy": "multi_step",
                    "analysis_result": analysis_result
                }
            except Exception as fallback_error:
                print(f"❌ Fallback planning also failed: {fallback_error}")
                error_msg = f"Planning failed: {e}. Fallback also failed: {fallback_error}"

        total_time = time.time() - start_time
        return {
            "plan": None,
            "plan_error": f"Multi-step planning error: {error_msg}",
            "last_node": "planner",
            "planning_time": total_time,
            "execution_strategy": "multi_step"
        }


def _handle_llm_fallback(normalized_query: str, analysis_result: dict, state: dict, call_llm_func, start_time: float) -> dict:
    """Handle fallback LLM planning for unknown query types."""
    print(f"🤖 Using LLM fallback planning...")

    # Safety check for call_llm_func
    if call_llm_func is None:
        print("❌ ERROR: call_llm_func is None in fallback, cannot proceed")
        return {
            "plan": None,
            "last_node": "planner",
            "planning_time": time.time() - start_time,
            "execution_strategy": "llm_fallback",
            "analysis_result": analysis_result,
            "error": "LLM function not available"
        }

    llm_start = time.time()

    # Use enhanced prompt with intent context
    try:
        planner_prompt = load_prompt('planner_enhanced')
    except:
        print("⚠️ Enhanced prompt not found, using standard planner")
        planner_prompt = load_prompt('planner')

    # Fill in the prompt template
    planner_prompt = planner_prompt.replace(
        '{intent}', json.dumps(analysis_result, indent=2))
    planner_prompt = planner_prompt.replace('{query}', normalized_query)

    messages = [
        {'role': 'system', 'content': planner_prompt},
        {'role': 'user', 'content': f"Generate plan for: {normalized_query}"}
    ]

    try:
        # Use Pro model for complex fallback planning
        print("🧠 Using Pro model for fallback planning")
        # Use codegen node config (Pro model) for complex reasoning
        llm_output = call_llm_func(state, messages, 'codegen')
        llm_time = time.time() - llm_start
        print(f"✅ LLM fallback completed in {llm_time:.2f}s")

        response_str = str(llm_output).strip()
        plan = json.loads(response_str)
        plan = _enforce_all_compartments(plan)

        # Apply safety flags
        plan = _apply_safety_flags(plan, analysis_result)

        total_time = time.time() - start_time

        print(f"✅ Generated fallback plan")
        print(f"⏱️ Total planning time: {total_time:.2f}s")
        print("*" * 60)

        return {
            "plan": plan,
            "last_node": "planner",
            "planning_time": total_time,
            "execution_strategy": "llm_fallback",
            "analysis_result": analysis_result
        }

    except Exception as e:
        print(f"❌ Fallback planning error: {e}")
        total_time = time.time() - start_time
        return {
            "plan": None,
            "plan_error": f"Fallback planning error: {e}",
            "last_node": "planner",
            "planning_time": total_time,
            "execution_strategy": "llm_fallback"
        }


def _enforce_all_compartments(p):
    """Ensure all list operations have all_compartments=True."""
    if isinstance(p, dict):
        if "action" in p and isinstance(p["action"], str) and p["action"].lower().startswith("list_"):
            params = p.get("params") or {}
            if not isinstance(params, dict):
                params = {}
            if not params.get("all_compartments", False):
                params["all_compartments"] = True
            p["params"] = params
        elif "steps" in p and isinstance(p["steps"], list):
            for step in p["steps"]:
                if isinstance(step, dict) and isinstance(step.get("action"), str) and step["action"].lower().startswith("list_"):
                    sparams = step.get("params") or {}
                    if not isinstance(sparams, dict):
                        sparams = {}
                    if not sparams.get("all_compartments", False):
                        sparams["all_compartments"] = True
                    step["params"] = sparams
    return p


def _convert_template_to_plan(template_plan: dict, analysis_result: dict) -> dict:
    """Convert a template plan to full execution plan."""
    resource = analysis_result.get('primary_resource')
    oci_service = analysis_result.get('oci_service', 'compute')
    api_method = template_plan.get('api_method')

    plan = {
        "action": api_method,
        "service": oci_service,
        "params": {
            "compartment_id": "${oci_creds.tenancy}",
            "all_compartments": True
        },
        "safety_tier": "safe"
    }

    # Add filtering if needed
    if template_plan.get('requires_filtering'):
        plan["filter_in_code"] = True
        plan["filters"] = template_plan.get('filters', [])

    return plan


def _apply_safety_flags(plan: dict, analysis_result: dict) -> dict:
    """
    Apply safety flags to the plan based on analysis results.
    Adds requires_confirmation and missing_parameters flags.
    """
    if not isinstance(plan, dict):
        return plan

    # Check if action is mutating
    is_mutating = analysis_result.get('is_mutating', False)
    action = plan.get('action', '')

    if is_mutating:
        print(f"⚠️ Mutating action detected: {action}")
        plan['requires_confirmation'] = True
        plan['safety_tier'] = 'destructive'

        # Check for missing parameters based on action type
        missing_params = []
        params = plan.get('params', {})

        if action == 'create_instance':
            required_params = ['compartment_id',
                               'shape', 'image_id', 'subnet_id']
            missing_params = [
                param for param in required_params if param not in params]
        elif action == 'create_bucket':
            required_params = ['compartment_id', 'name']
            missing_params = [
                param for param in required_params if param not in params]
        elif action == 'create_volume':
            required_params = ['compartment_id', 'size_in_gbs']
            missing_params = [
                param for param in required_params if param not in params]
        elif action == 'create_load_balancer':
            required_params = ['compartment_id', 'shape_name', 'subnet_ids']
            missing_params = [
                param for param in required_params if param not in params]

        if missing_params:
            plan['missing_parameters'] = missing_params
            print(f"⚠️ Missing parameters: {missing_params}")
        else:
            print(f"✅ All required parameters present")
    else:
        print(f"✅ Safe action: {action}")
        plan['safety_tier'] = 'safe'

    return plan
