# core/llm_manager.py
import os
import time
import streamlit as st
from pydantic import SecretStr
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic

# ============================================================================
# NODE-SPECIFIC MODEL CONFIGURATION (Multi-Provider)
# ============================================================================
# Fast models for most nodes, powerful models for codegen only
NODE_MODEL_CONFIG = {
    'normalizer': 'fast',     # Fast normalization
    'planner': 'fast',         # Fast planning (simple tasks)
    'codegen': 'powerful',     # ONLY codegen uses powerful model
    'verifier': 'fast',        # Fast verification
    'presentation': 'fast',    # Fast presentation
    'final_presentation_summary': 'fast',
    'intent_analyzer': 'fast'  # Fast intent analysis
}

# Provider-specific model mappings
PROVIDER_MODELS = {
    'gemini': {
        'fast': 'gemini-2.5-flash',
        'powerful': 'gemini-2.5-pro'
    },
    'openai': {
        'fast': 'gpt-4o-mini',
        'powerful': 'gpt-4o'
    },
    'anthropic': {
        'fast': 'claude-3-5-haiku-20241022',
        'powerful': 'claude-3-5-sonnet-20241022'
    },
    'groq': {
        'fast': 'llama-3.3-70b-versatile',
        'powerful': 'llama-3.3-70b-versatile'  # Groq has limited models
    }
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
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    model_name = model_name or "gpt-4o"
    print(f"   Using OpenAI model: {model_name}")
    llm = ChatOpenAI(api_key=api_key, model=model_name, temperature=0.1)
    response = llm.invoke(_to_lc_messages(messages))
    return response.content


def _call_gemini(messages, model_name=None):
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    if model_name is None:
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
    print(f"   Using Gemini model: {model_name}")
    llm = ChatGoogleGenerativeAI(api_key=SecretStr(
        api_key), model=model_name, temperature=0.1)
    response = llm.invoke(_to_lc_messages(messages))
    return response.content


def _call_groq(messages, model_name=None):
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    model_name = model_name or "llama-3.3-70b-versatile"
    print(f"   Using Groq model: {model_name}")
    llm = ChatGroq(api_key=SecretStr(api_key),
                   model=model_name, temperature=0.1)
    response = llm.invoke(_to_lc_messages(messages))
    return response.content


def _call_anthropic(messages, model_name=None):
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    model_name = model_name or "claude-3-5-sonnet-20241022"
    print(f"   Using Anthropic model: {model_name}")
    llm = ChatAnthropic(api_key=api_key, model=model_name, temperature=0.1)
    response = llm.invoke(_to_lc_messages(messages))
    return response.content


def call_llm(state, messages, node_name='node', use_fast_model=False):
    """
    Call LLM with node-specific model selection across all providers.

    Args:
        state: Agent state
        messages: Messages to send
        node_name: Name of calling node (normalizer, planner, codegen, etc.)
        use_fast_model: If True, use fast/cheap models (for intent analysis, etc.)
    """
    print(f"DEBUG: call_llm called with node_name: {node_name}")
    print(f"DEBUG: call_llm messages count: {len(messages)}")
    start_time = time.time()

    # Get node model preference (fast/powerful)
    node_model_type = NODE_MODEL_CONFIG.get(node_name, 'fast')
    print(f"🎯 Node '{node_name}' → Model type: {node_model_type}")

    # Get user's preferred provider
    llm_preference = state.get("llm_preference", {})
    selected_provider = llm_preference.get("provider", "gemini")
    print(f"🔧 Selected provider: {selected_provider}")

    # Get the specific model for this provider and node type
    provider_models = PROVIDER_MODELS.get(selected_provider, {})
    specific_model = provider_models.get(node_model_type)

    if not specific_model:
        print(
            f"⚠️ No model configured for {selected_provider}/{node_model_type}, using defaults")
        # Fallback to default models
        if selected_provider == 'gemini':
            specific_model = 'gemini-2.5-flash' if node_model_type == 'fast' else 'gemini-2.5-pro'
        elif selected_provider == 'openai':
            specific_model = 'gpt-4o-mini' if node_model_type == 'fast' else 'gpt-4o'
        elif selected_provider == 'anthropic':
            specific_model = 'claude-3-5-haiku-20241022' if node_model_type == 'fast' else 'claude-3-5-sonnet-20241022'
        elif selected_provider == 'groq':
            specific_model = 'llama-3.3-70b-versatile'

    print(f"🎯 Using {selected_provider} model: {specific_model}")

    # All available providers with priority order
    all_providers = ['gemini', 'openai', 'anthropic', 'groq']

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

            # Get the model for this provider and node type
            provider_models = PROVIDER_MODELS.get(current_provider, {})
            model_to_use = provider_models.get(node_model_type)

            if not model_to_use:
                # Use defaults if not configured
                if current_provider == 'gemini':
                    model_to_use = 'gemini-2.5-flash' if node_model_type == 'fast' else 'gemini-2.5-pro'
                elif current_provider == 'openai':
                    model_to_use = 'gpt-4o-mini' if node_model_type == 'fast' else 'gpt-4o'
                elif current_provider == 'anthropic':
                    model_to_use = 'claude-3-5-haiku-20241022' if node_model_type == 'fast' else 'claude-3-5-sonnet-20241022'
                elif current_provider == 'groq':
                    model_to_use = 'llama-3.3-70b-versatile'

            print(f"   Using {current_provider} model: {model_to_use}")

            # Call the appropriate provider
            if current_provider == 'gemini':
                result = _call_gemini(messages, model_name=model_to_use)
            elif current_provider == 'openai':
                result = _call_openai(messages, model_name=model_to_use)
            elif current_provider == 'anthropic':
                result = _call_anthropic(messages, model_name=model_to_use)
            elif current_provider == 'groq':
                result = _call_groq(messages, model_name=model_to_use)

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
                    'model': model_to_use,
                    'provider': current_provider
                }
            except:
                pass

            print(
                f"DEBUG: Returning result from {current_provider}: {type(result)}")
            return result

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
