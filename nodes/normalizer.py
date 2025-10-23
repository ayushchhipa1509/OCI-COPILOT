# nodes/normalizer.py
from core.state import AgentState
from core.prompts import load_prompt
from core.llm_manager import call_llm as default_call_llm
import json
import re


def normalizer_node(state: AgentState) -> dict:
    """
    Simplified normalizer that normalizes queries and routes based on toggle.
    - Normalizes the query (typo correction, standardization)
    - Routes based on use_rag_chain toggle (no LLM routing decision)
    """
    print("-" * 60)
    print("🔄 NORMALIZER NODE - STARTING")
    print("-" * 60)

    user_input = state.get("user_input", "").strip()
    if not user_input:
        return {"next_step": "presentation_node", "last_node": "normalizer"}

    call_llm_func = state.get("call_llm", default_call_llm)
    prompt = load_prompt('normalizer')

    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': user_input}
    ]

    try:
        llm_response = call_llm_func(state, messages, 'normalizer')
        print(f"🔍 Raw normalizer response: {llm_response}")

        # Extract JSON from the response
        json_match = re.search(r'\{.*\}', str(llm_response), re.DOTALL)
        if not json_match:
            raise ValueError("LLM response did not contain valid JSON.")

        response_json = json.loads(json_match.group(0))
        normalized_query = response_json.get("normalized_query", user_input)

        print(f"✅ Normalizer corrected query: '{normalized_query}'")
        print(f"🔍 Normalizer response JSON: {response_json}")

        # Check if query is executable (OCI operation) or non-executable (chat/question)
        is_executable = response_json.get("is_executable", False)
        intent = response_json.get("intent", "unknown")

        print(f"🔍 Is executable: {is_executable}")
        print(f"🔍 Intent: {intent}")

        if not is_executable:
            print("🔄 Non-executable query detected, routing to presentation")
            return {
                "user_input": normalized_query,
                "normalized_query": normalized_query,
                "next_step": "presentation_node",
                "last_node": "normalizer",
                "intent": "general_chat"
            }

        # Route based on toggle for executable queries
        # Default to OFF as per user request
        use_rag_chain = state.get("use_rag_chain", False)
        if use_rag_chain:
            route = "rag_retriever"
            print(f"✅ Executable query + RAG toggle ON. Routing to: {route}")
        else:
            route = "planner"
            print(f"✅ Executable query + RAG toggle OFF. Routing to: {route}")

        return {
            "user_input": normalized_query,
            "normalized_query": normalized_query,
            "next_step": route,
            "last_node": "normalizer"
        }

    except Exception as e:
        print(f"⚠️ Normalizer error, using fallback routing: {e}")
        # For fallback, assume it's executable and use toggle
        use_rag_chain = state.get("use_rag_chain", False)  # Default to OFF
        route = "rag_retriever" if use_rag_chain else "planner"

        return {
            "user_input": user_input,
            "normalized_query": user_input,
            "next_step": route,
            "last_node": "normalizer"
        }
    finally:
        print("-" * 60)
        print("🔄 NORMALIZER NODE - COMPLETED")
        print("-" * 60)
