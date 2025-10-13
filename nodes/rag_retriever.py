# nodes/rag_retriever.py

from core.state import AgentState
from rag.retriever import retrieve


def rag_retriever_node(state: AgentState) -> dict:
    """
    RAG Retriever node for semantic search.
    Queries the vector store with the user input and returns the results.
    If no relevant data is found, routes to planner chain as fallback.
    """
    # The retrieve function from rag.retriever expects the full state
    results = retrieve(state)

    rag_found = results.get("rag_found", False)
    rag_result = results.get("rag_result", []) if rag_found else []
    rag_metadata = results.get("rag_metadata", []) if rag_found else []

    print(f"🧠 RAG Retriever - Found Relevant Docs: {rag_found}")
    print(f"🧠 RAG Retriever - Document Count: {len(rag_result)}")
    if rag_result:
        print(f"🧠 RAG Retriever - First Doc Preview: {rag_result[0][:100]}...")

    # Check if we have meaningful data
    has_data = rag_found and len(rag_result) > 0 and any(
        doc.strip() for doc in rag_result if isinstance(doc, str)
    )

    if has_data:
        print("✅ RAG found relevant data - proceeding to presentation")
        # Prepare a consumable execution_result for downstream nodes
        execution_result = {
            "data": rag_result,
            "metadatas": rag_metadata
        }
        # Route to presentation with RAG data
        out = results.copy()
        out["execution_result"] = execution_result
        out["next_step"] = "presentation_node"
        out["execution_strategy"] = "rag_chain"
    else:
        print("⚠️ RAG found no relevant data - falling back to planner chain")
        # Route to planner chain as fallback
        out = results.copy()
        out["next_step"] = "planner"
        out["execution_strategy"] = "rag_fallback_to_planner"
        out["rag_fallback"] = True
        # CRITICAL: Preserve the normalized query for planner
        out["normalized_query"] = state.get(
            "normalized_query", state.get("user_input", ""))

    return out
