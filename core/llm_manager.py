# core/llm_manager.py
import os
import time
import streamlit as st
from pydantic import SecretStr
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# ============================================================================
# NODE-SPECIFIC MODEL CONFIGURATION (Gemini Only)
# ============================================================================
NODE_MODEL_CONFIG = {
    'normalizer': 'gemini-2.5-flash',     # Fast normalization
    'planner': 'gemini-2.5-flash',        # Fast planning (simple tasks)
    'codegen': 'gemini-2.5-pro',          # ONLY codegen uses Pro model
    'verifier': 'gemini-2.5-flash',       # Fast verification
    'presentation': 'gemini-2.5-flash',   # Fast presentation
    # Fast presentation (actual node name)
    'final_presentation_summary': 'gemini-2.5-flash',
    'intent_analyzer': 'gemini-2.5-flash'  # Fast intent analysis
}


def _to_lc_messages(messages):
    lc_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            lc_messages.append(SystemMessage(content=msg['content']))
        elif msg['role'] == 'user':
            lc_messages.append(HumanMessage(content=msg['content']))
    return lc_messages


def _call_openai(messages, model_name=None):
    # OpenAI disabled - redirect to Gemini
    print(f"   OpenAI disabled - redirecting to Gemini")
    return _call_gemini(messages)


def _call_gemini(messages):
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
    print(f"   Using Gemini model: {model_name}")
    llm = ChatGoogleGenerativeAI(api_key=SecretStr(
        api_key), model=model_name, temperature=0.1)
    response = llm.invoke(_to_lc_messages(messages))
    return response.content


def _call_groq(messages):
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    model_name = "llama-3.3-70b-versatile"
    llm = ChatGroq(api_key=SecretStr(api_key),
                   model=model_name, temperature=0.1)
    response = llm.invoke(_to_lc_messages(messages))
    return response.content


def call_llm(state, messages, node_name='node', use_fast_model=False):
    """
    Call LLM with node-specific model selection.

    Args:
        state: Agent state
        messages: Messages to send
        node_name: Name of calling node (normalizer, planner, codegen, etc.)
        use_fast_model: If True, use fast/cheap models (for intent analysis, etc.)
    """
    print(f"DEBUG: call_llm called with node_name: {node_name}")
    print(f"DEBUG: call_llm messages count: {len(messages)}")
    start_time = time.time()

    # Check if node has specific model configured
    node_model = NODE_MODEL_CONFIG.get(node_name)

    if node_model:
        # Use node-specific Gemini model
        print(f"🎯 Node '{node_name}' → Using configured model: {node_model}")
        try:
            result = _call_gemini(messages)
            elapsed = time.time() - start_time
            print(f"✅ {node_name} completed in {elapsed:.2f}s")
            print(
                f"DEBUG: LLM result type: {type(result)}, length: {len(str(result)) if result else 'None'}")

            # Update UI status if possible
            try:
                if 'node_status' not in st.session_state:
                    st.session_state.node_status = {}
                st.session_state.node_status[node_name] = {
                    'status': 'completed',
                    'time': elapsed,
                    'model': node_model
                }
            except:
                pass

            print(
                f"DEBUG: Returning result from node-specific model: {type(result)}")
            return result
        except Exception as e:
            print(f"❌ Node '{node_name}' with {node_model} failed: {e}")
            # Fall through to original fallback logic

    # Original fallback logic for nodes without specific config
    llm_preference = state.get("llm_preference", {})

    # Smart model selection based on task
    if use_fast_model:
        selected_provider = "gemini"
        print(
            f"⚡ call_llm using FAST model for node '{node_name}': {selected_provider}")
    else:
        selected_provider = llm_preference.get("provider", "gemini")
        print(
            f"🔧 call_llm selected provider for node '{node_name}': {selected_provider}")

    # All available providers (Gemini first, then Groq as fallback)
    all_providers = ['gemini', 'groq']

    # Create fallback order: selected provider first, then others
    providers_to_try = [selected_provider]
    for provider in all_providers:
        if provider != selected_provider:
            providers_to_try.append(provider)

    print(f"🔄 Fallback order: {providers_to_try}")

    last_error = None

    for current_provider in providers_to_try:
        try:
            if current_provider == selected_provider:
                print(f"🎯 Trying PRIMARY provider: {current_provider}")
            else:
                print(f"🔄 Trying FALLBACK provider: {current_provider}")

            if current_provider == 'gemini':
                return _call_gemini(messages)
            elif current_provider == 'groq':
                return _call_groq(messages)

        except Exception as e:
            last_error = e
            error_msg = str(e)

            # Check for rate limit errors
            if "ResourceExhausted" in error_msg or "429" in error_msg or "quota" in error_msg.lower():
                print(f"⚠️ Rate limit exceeded for '{current_provider}': {e}")
            else:
                if current_provider == selected_provider:
                    print(
                        f"❌ PRIMARY provider '{current_provider}' failed: {e}")
                else:
                    print(
                        f"❌ FALLBACK provider '{current_provider}' failed: {e}")
            continue

    # If all providers failed
    error_message = f"All LLM providers failed at node '{node_name}'. Selected: {selected_provider}. Last error: {last_error}"
    print(f"DEBUG: LLM call failed, returning error: {error_message}")
    st.error(error_message)
    return f"[ERROR: {error_message}]"
