# core/graph.py
from langgraph.graph import StateGraph, END
from core.state import AgentState

# Import all node functions
from nodes.supervisor import supervisor_node
from nodes.normalizer import normalizer_node
from nodes.planner import planner_node
from nodes.codegen_node import codegen_node
from nodes.verifier import verifier_node
from nodes.executor import executor_node
from nodes.rag_retriever import rag_retriever_node
# Import the new presentation node
from nodes.presentation_node import presentation_node
# Import memory nodes
from nodes.memory_context import memory_context_node
from nodes.memory_manager import memory_manager_node


def build_graph():
    graph = StateGraph(AgentState)

    # Define all nodes in the new architecture
    # Memory loading (first)
    graph.add_node("memory_context", memory_context_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("normalizer", normalizer_node)
    graph.add_node("rag_retriever", rag_retriever_node)
    graph.add_node("planner", planner_node)
    graph.add_node("codegen", codegen_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("executor", executor_node)
    graph.add_node("presentation_node", presentation_node)
    # Memory saving (last)
    graph.add_node("memory_manager", memory_manager_node)

    # Set the entry point to memory_context (loads memory first)
    graph.set_entry_point("memory_context")

    # 0. Memory context always goes to supervisor
    graph.add_edge("memory_context", "supervisor")

    # 1. Supervisor routes to normalizer, presentation, planner, or codegen (for retries)
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_step", "normalizer"),
        {
            "normalizer": "normalizer",
            "presentation_node": "presentation_node",
            "planner": "planner",  # For planner retries
            "codegen": "codegen"  # For retry loops
        }
    )

    # 2. Normalizer routes based on toggle (RAG or Planner)
    graph.add_conditional_edges(
        "normalizer",
        lambda state: state.get("next_step"),
        {
            "rag_retriever": "rag_retriever",
            "planner": "planner",
            "presentation_node": "presentation_node"  # For non-executable queries
        }
    )

    # 3. RAG chain - with fallback to planner
    graph.add_conditional_edges(
        "rag_retriever",
        lambda state: state.get("next_step", "presentation_node"),
        {
            "presentation_node": "presentation_node",  # RAG found data
            "planner": "planner"  # RAG fallback to planner
        }
    )

    # 4. Planner chain logic - route through supervisor for parameter checking
    graph.add_conditional_edges(
        "planner",
        lambda state: state.get("next_step", "supervisor"),
        {
            "supervisor": "supervisor",  # Check for missing parameters
            "codegen": "codegen",  # Direct to codegen if no issues
            "planner": "planner",  # Retry planner if needed
            "presentation_node": "presentation_node"  # Error handling
        }
    )
    graph.add_edge("codegen", "verifier")

    # 5. Verifier is the control gate for execution
    graph.add_conditional_edges(
        "verifier",
        # The verifier node itself now sets the next_step
        lambda state: state.get("next_step"),
        {
            "executor": "executor",
            "presentation_node": "presentation_node"  # On failure, show error to user
        }
    )

    # 6. Executor routes based on success/failure
    graph.add_conditional_edges(
        "executor",
        # Always go to presentation (success or failure)
        lambda state: "presentation_node",
        {
            "presentation_node": "presentation_node"  # Show results to user
        }
    )

    # 7. Presentation node routes to memory manager (save memory) or END
    graph.add_conditional_edges(
        "presentation_node",
        lambda state: "memory_manager" if state.get(
            "memory_saved") is None else "END",
        {
            "memory_manager": "memory_manager",
            "END": END
        }
    )

    # 8. Memory manager saves memory and ends the turn
    graph.add_edge("memory_manager", END)

    # Compile the final, executable graph
    return graph.compile()
