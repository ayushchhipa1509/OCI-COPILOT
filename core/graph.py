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


def build_graph():
    graph = StateGraph(AgentState)

    # Define all nodes in the new architecture
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("normalizer", normalizer_node)
    graph.add_node("rag_retriever", rag_retriever_node)
    graph.add_node("planner", planner_node)
    graph.add_node("codegen", codegen_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("executor", executor_node)
    graph.add_node("presentation_node", presentation_node)

    # Set the entry point
    graph.set_entry_point("supervisor")

    # 1. Supervisor routes to normalizer, presentation, or codegen (for retries)
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_step", "normalizer"),
        {
            "normalizer": "normalizer",
            "presentation_node": "presentation_node",
            "codegen": "codegen"  # For retry loops
        }
    )

    # 2. Normalizer routes based on toggle (RAG or Planner)
    graph.add_conditional_edges(
        "normalizer",
        lambda state: state.get("next_step"),
        {
            "rag_retriever": "rag_retriever",
            "planner": "planner"
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

    # 4. Planner chain logic
    graph.add_edge("planner", "codegen")
    graph.add_edge("codegen", "verifier")

    # 5. Verifier is the control gate for execution
    graph.add_conditional_edges(
        "verifier",
        # The verifier node itself now sets the next_step
        lambda state: state.get("next_step"),
        {
            "executor": "executor",
            "supervisor": "supervisor"  # On failure, loop back to supervisor for review
        }
    )

    # 6. Executor routes based on success/failure
    graph.add_conditional_edges(
        "executor",
        lambda state: "supervisor" if state.get(
            "execution_error") else "presentation_node",
        {
            "presentation_node": "presentation_node",  # Success - go to presentation
            "supervisor": "supervisor"  # Failure - loop back to supervisor for retry
        }
    )

    # 7. Presentation node is the final step before END
    graph.add_edge("presentation_node", END)

    # Compile the final, executable graph
    return graph.compile()
