# core/state.py
from typing import TypedDict, Any, Dict, List, Optional, Union


class AgentState(TypedDict, total=False):
    # --- Core session info ---
    user_input: str
    session_id: str
    chat_history: List[str]

    # --- Control Flow & Routing ---
    next_step: Optional[str]
    last_node: Optional[str]
    intent: Optional[str]
    use_rag_chain: bool  # Toggle for RAG vs Planner routing

    # --- Planning & Verification (from planner_chain) ---
    normalized_query: Optional[str]
    plan: Optional[Dict[str, Any]]
    plan_error: Optional[str]
    plan_valid: bool
    verify_retries: int

    # --- Safety & Execution ---
    safety_decision: str
    requires_confirmation: bool
    execution_result: Optional[Union[Dict[str, Any], List[Any]]]
    execution_error: Optional[str]

    # --- Post-Processing ---
    analytics: Optional[Dict[str, Any]]
    analyze_type: Optional[str]

    # --- Memory ---
    memory_saved: bool
    short_term_memory: Optional[Dict[str, Any]]

    # --- Presentation ---
    presentation: Optional[Union[str, Dict[str, Any]]]

    # --- RAG (Retrieval-Augmented Generation) ---
    rag_found: bool
    rag_result: Optional[List[str]]
    rag_metadata: Optional[List[Dict[str, Any]]]
    data_source: Optional[str]  # "rag_cache" or "live_api"
    bypass_memory: bool  # Skip memory_manager for RAG flow
    analytics_only: bool  # Go directly to final after analytics
    rag_fallback: bool  # True when RAG falls back to planner
    # "rag_chain", "rag_fallback_to_planner", "planner_chain", etc.
    execution_strategy: Optional[str]

    # --- OCI & LLM Config ---
    oci_creds: Dict[str, Any]
    llm_preference: Dict[str, Any]
    call_llm: Any
    db_path: str

    # --- Code Generation ---
    generated_code: Optional[str]

    # --- Performance Tracking ---
    timings: Optional[Dict[str, float]]  # Per-node execution times
    planning_time: Optional[float]  # Time spent in planner
    total_execution_time: Optional[float]  # Total query processing time
