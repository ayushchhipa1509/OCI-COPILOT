# core/graph_visualizer.py - Enhanced Graph Visualization

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List
import streamlit as st


class GraphVisualizer:
    """Enhanced graph visualizer with clean flowchart layout."""

    def __init__(self):
        self.node_colors = {
            'supervisor': '#FF6B6B',      # Red - Entry point
            'normalizer': '#4ECDC4',     # Teal - Router
            'rag_retriever': '#45B7D1',  # Blue - RAG chain
            'planner': '#96CEB4',        # Green - Planner chain
            'codegen': '#FFEAA7',        # Yellow - Code generation
            'verifier': '#DDA0DD',       # Plum - Verification
            'executor': '#98D8C8',       # Mint - Execution
            'presentation_node': '#F7DC6F'  # Gold - Final output
        }

    def create_flowchart(self) -> nx.DiGraph:
        """Create a clean flowchart of the agent architecture."""
        G = nx.DiGraph()

        # Add nodes with positions for clean vertical layout
        nodes = [
            ('supervisor', (0, 0)),
            ('normalizer', (0, -1.5)),
            ('rag_retriever', (-2.5, -3)),
            ('planner', (2.5, -3)),
            ('codegen', (2.5, -4.5)),
            ('verifier', (2.5, -6)),
            ('executor', (2.5, -7.5)),
            ('presentation_node', (0, -9))
        ]

        for node, pos in nodes:
            G.add_node(node, pos=pos)

        # Add edges including self-correction loops
        edges = [
            # Main flow
            ('supervisor', 'normalizer'),
            ('supervisor', 'presentation_node'),
            ('normalizer', 'rag_retriever'),
            ('normalizer', 'planner'),
            ('rag_retriever', 'presentation_node'),
            ('rag_retriever', 'planner'),  # RAG fallback to planner
            ('planner', 'codegen'),
            ('codegen', 'verifier'),
            ('verifier', 'executor'),
            ('executor', 'presentation_node'),

            # Self-correction loops
            ('verifier', 'supervisor'),  # Syntax error loop
            ('executor', 'supervisor'),  # Runtime error loop
            ('supervisor', 'codegen')    # Retry to codegen
        ]

        G.add_edges_from(edges)

        return G

    def draw_flowchart(self, figsize=(10, 12)) -> plt.Figure:
        """Draw the flowchart with enhanced styling."""
        G = self.create_flowchart()
        pos = nx.get_node_attributes(G, 'pos')

        fig, ax = plt.subplots(figsize=figsize, facecolor='white')

        # Draw nodes with custom styling
        for node in G.nodes():
            color = self.node_colors.get(node, '#CCCCCC')
            nx.draw_networkx_nodes(G, pos, nodelist=[node],
                                   node_color=color, node_size=3000,
                                   alpha=0.9, ax=ax, node_shape='o',
                                   edgecolors='black', linewidths=2)

        # Draw edges with different styles
        edge_styles = {
            # Main flow
            ('supervisor', 'normalizer'): {'color': '#FF6B6B', 'width': 3, 'style': 'solid'},
            ('supervisor', 'presentation_node'): {'color': '#FF6B6B', 'width': 2, 'style': 'dashed'},
            ('normalizer', 'rag_retriever'): {'color': '#45B7D1', 'width': 3, 'style': 'solid'},
            ('normalizer', 'planner'): {'color': '#96CEB4', 'width': 3, 'style': 'solid'},
            ('rag_retriever', 'presentation_node'): {'color': '#45B7D1', 'width': 3, 'style': 'solid'},
            # RAG fallback
            ('rag_retriever', 'planner'): {'color': '#FFD700', 'width': 2, 'style': 'dashed'},
            ('planner', 'codegen'): {'color': '#96CEB4', 'width': 2, 'style': 'solid'},
            ('codegen', 'verifier'): {'color': '#96CEB4', 'width': 2, 'style': 'solid'},
            ('verifier', 'executor'): {'color': '#96CEB4', 'width': 2, 'style': 'solid'},
            ('executor', 'presentation_node'): {'color': '#96CEB4', 'width': 3, 'style': 'solid'},

            # Self-correction loops
            # Syntax error loop
            ('verifier', 'supervisor'): {'color': '#FF8C00', 'width': 2, 'style': 'dotted'},
            # Runtime error loop
            ('executor', 'supervisor'): {'color': '#DC143C', 'width': 2, 'style': 'dotted'},
            # Retry to codegen
            ('supervisor', 'codegen'): {'color': '#32CD32', 'width': 2, 'style': 'dotted'}
        }

        for edge, style in edge_styles.items():
            if edge in G.edges():
                nx.draw_networkx_edges(
                    G, pos, edgelist=[edge],
                    edge_color=style['color'],
                    width=style['width'],
                    style=style['style'],
                    alpha=0.8,
                    arrowsize=20,
                    arrowstyle='->',
                    ax=ax
                )

        # Draw labels with better formatting
        labels = {
            'supervisor': '🧠\nSupervisor',
            'normalizer': '🔄\nNormalizer',
            'rag_retriever': '🧠\nRAG\nRetriever',
            'planner': '⚙️\nPlanner',
            'codegen': '💻\nCode\nGenerator',
            'verifier': '✅\nVerifier',
            'executor': '🚀\nExecutor',
            'presentation_node': '📊\nPresentation'
        }

        nx.draw_networkx_labels(G, pos, labels, font_size=9,
                                font_weight='bold', ax=ax)

        # Add title
        ax.text(0, 1, '🤖 OCI Copilot Agent Architecture',
                ha='center', va='top', fontsize=14, fontweight='bold')

        # Create legend
        legend_elements = [
            mpatches.Patch(color='#FF6B6B', label='Supervisor Flow'),
            mpatches.Patch(color='#45B7D1', label='RAG Chain (Toggle ON)'),
            mpatches.Patch(color='#96CEB4',
                           label='Planner Chain (Toggle OFF)'),
            mpatches.Patch(color='#FFD700', label='RAG Fallback to Planner'),
            mpatches.Patch(color='#FF8C00', label='Syntax Error Loop'),
            mpatches.Patch(color='#DC143C', label='Runtime Error Loop'),
            mpatches.Patch(color='#32CD32', label='Retry to Codegen')
        ]

        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

        # Clean up
        ax.set_xlim(-4, 4)
        ax.set_ylim(-10, 1.5)
        ax.axis('off')

        plt.tight_layout()
        return fig


def draw_agent_flowchart():
    """Draw the agent flowchart in Streamlit."""
    try:
        visualizer = GraphVisualizer()
        fig = visualizer.draw_flowchart()
        st.pyplot(fig)

        # Show chain information in columns
        st.markdown("---")
        st.subheader("📋 Chain Details")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧠 RAG Chain (Toggle ON)")
            st.markdown("""
            - ✅ Uses cached data from vector store
            - ⚡ Fast response time
            - 📚 Historical data queries
            - 🔒 Read-only, safe operations
            - **Flow:** RAG Retriever → Presentation
            """)

        with col2:
            st.markdown("### ⚙️ Planner Chain (Toggle OFF)")
            st.markdown("""
            - 🔄 Executes live OCI operations
            - 🐌 Slower (API calls)
            - 📊 Real-time data
            - ⚠️ Can modify resources
            - **Flow:** Planner → Codegen → Verifier → Executor → Presentation
            - **🔄 Self-Correction:** Automatic retry on errors
            - **🔄 RAG Fallback:** Receives queries when RAG finds no data
            """)

        # Show routing logic
        st.markdown("---")
        st.subheader("🎯 Routing Logic")
        st.markdown("""
        1. **User Query** → 🧠 Supervisor
        2. **Supervisor Analysis:**
           - Non-executable query → 📊 Direct to Presentation
           - Executable query → 🔄 Normalizer
        3. **Normalizer** → Normalizes query & checks toggle
           - Toggle ON → 🧠 RAG Chain
           - Toggle OFF → ⚙️ Planner Chain
        4. **Chains are DISCONNECTED** for testing
        5. Both chains end at → 📊 Presentation
        """)

        # Show self-correction loops
        st.markdown("---")
        st.subheader("🔄 Self-Correction Loops")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🟠 Syntax Error Loop")
            st.markdown("""
            **Trigger:** Verifier detects syntax/structure errors
            
            **Flow:** 
            1. Verifier → Supervisor (with error details)
            2. Supervisor → Codegen (with correction feedback)
            3. Codegen generates fixed code
            4. Process continues normally
            
            **Retry Limit:** 1 attempt
            """)

        with col2:
            st.markdown("### 🔴 Runtime Error Loop")
            st.markdown("""
            **Trigger:** Executor encounters runtime errors
            
            **Flow:**
            1. Executor → Supervisor (with error details)
            2. Supervisor → Codegen (with execution feedback)
            3. Codegen generates corrected code
            4. Process continues normally
            
            **Smart Classification:** Only retries code-related errors
            **Retry Limit:** 1 attempt
            """)

        st.markdown("### 🎯 Benefits")
        st.markdown("""
        - **⚡ Fast Model First:** Uses gpt-4o for speed, retries with context on failure
        - **🧠 Automated Debugging:** AI learns from its own mistakes
        - **🛡️ Robust Error Handling:** Prevents infinite loops with smart limits
        - **💰 Cost Effective:** Most queries succeed on first try
        """)

        # Show RAG fallback mechanism
        st.markdown("---")
        st.subheader("🔄 RAG Fallback Mechanism")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🟡 RAG Fallback Flow")
            st.markdown("""
            **Trigger:** RAG finds no relevant data
            
            **Flow:**
            1. RAG Retriever checks vector store
            2. No relevant documents found
            3. Routes to Planner with normalized query
            4. Planner processes query normally
            5. Continues through Planner chain
            
            **Benefits:**
            - **Seamless fallback** when RAG has no data
            - **No data loss** - planner gets original query
            - **Automatic routing** - no user intervention needed
            """)

        with col2:
            st.markdown("### 🎯 Smart Routing")
            st.markdown("""
            **RAG Success:**
            - Found relevant data → Presentation Node
            - Fast, cached results
            
            **RAG Fallback:**
            - No relevant data → Planner Chain
            - Live API execution
            - Fresh, real-time results
            
            **Result:** Users always get answers!
            """)

    except Exception as e:
        st.error(f"Failed to draw flowchart: {e}")
        st.info("Make sure matplotlib and networkx are installed.")
