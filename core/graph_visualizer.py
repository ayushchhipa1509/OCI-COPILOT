# core/graph_visualizer.py - Professional Supervisor-Centric Architecture Visualization

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from typing import Dict, List
import numpy as np


class GraphVisualizer:
    """
    Professional supervisor-centric radial graph visualizer with polished styling,
    optimized visual hierarchy, and enhanced readability matching production-grade diagrams.
    """

    def __init__(self):
        # Optimized radial positions for better visual balance with more spacing
        self.node_positions = {
            'start': (0, 8.5),                 # START node at top
            'memory_context': (0, 6.5),        # Top - input memory
            'supervisor': (0, 0),              # Center - command hub
            'normalizer': (-5, 4),             # Upper-left
            'rag_retriever': (-6.5, 0),        # Far left
            'planner': (5, 4),                 # Upper-right
            'codegen': (6.5, 0),               # Far right
            'verifier': (5, -2.5),             # Mid-right-lower
            # Right side of presentation, near verifier
            'executor': (4, -4.5),
            'presentation_node': (0, -4.5),    # Bottom-center
            'memory_manager': (0, -6.5),       # Bottom - output memory
            'end': (0, -8.5),                  # END node at bottom
        }

        # Professional color palette with better contrast
        self.node_colors = {
            'start': '#27AE60',                # Green for start
            'memory_context': '#5DADE2',       # Sky Blue
            'supervisor': '#9B59B6',           # Rich Purple
            'normalizer': '#48C9B0',           # Turquoise
            'rag_retriever': '#2E4053',        # Dark Navy
            'planner': '#52BE80',              # Forest Green
            'codegen': '#F4D03F',              # Golden Yellow
            'verifier': '#E67E22',             # Burnt Orange
            'executor': '#E74C3C',             # Crimson Red
            'presentation_node': '#58D68D',    # Lime Green
            'memory_manager': '#85C1E9',       # Light Blue
            'end': '#C0392B',                  # Red for end
        }

        # Node shapes (matplotlib markers)
        self.node_shapes = {
            'start': 'o',
            'memory_context': 'o',
            'supervisor': 'd',              # Diamond for decision node
            'normalizer': 'o',
            'rag_retriever': 'o',
            'planner': 'o',
            'codegen': 's',                 # Square for processing
            'verifier': 's',
            'executor': 's',
            'presentation_node': 'o',
            'memory_manager': 'o',
            'end': 'o',
        }

        # Node sizes - MASSIVE for maximum visibility
        self.node_sizes = {
            'start': 15000,
            'supervisor': 35000,            # HUGE supervisor
            'memory_context': 18000,
            'normalizer': 18000,
            'rag_retriever': 18000,
            'planner': 18000,
            'codegen': 18000,
            'verifier': 18000,
            'executor': 18000,
            'presentation_node': 18000,
            'memory_manager': 18000,
            'end': 15000,
        }

        # Enhanced labels with emojis and better formatting
        self.node_labels = {
            'start': '▶️\nSTART',
            'memory_context': '⚖️\nLoad Memory',
            'supervisor': '👀\nSupervisor',
            'normalizer': '🔍\nNormalizer',
            'rag_retriever': '📚\nRAG\nRetriever',
            'planner': '📋\nPlanner',
            'codegen': '💻\nCodegen',
            'verifier': '✓\nVerifier',
            'executor': '🚀\nExecutor',
            'presentation_node': '🗣️\nPresentation',
            'memory_manager': '💾\nSave Memory',
            'end': '⏹️\nEND',
        }

    def create_graph(self) -> nx.DiGraph:
        """Create the directed graph with all architectural nodes and edges."""
        G = nx.DiGraph()

        # Add nodes
        for node in self.node_positions.keys():
            G.add_node(node)

        # Primary flow edges
        primary_edges = [
            ('start', 'memory_context'),           # START connects to memory
            ('memory_context', 'supervisor'),
            ('supervisor', 'normalizer'),
            ('normalizer', 'rag_retriever'),
            ('normalizer', 'planner'),
            ('rag_retriever', 'presentation_node'),
            ('planner', 'codegen'),
            ('codegen', 'verifier'),
            ('verifier', 'executor'),
            ('executor', 'presentation_node'),
            ('presentation_node', 'memory_manager'),
            # Memory manager connects to END
            ('memory_manager', 'end'),
        ]

        # Conditional/fallback edges
        conditional_edges = [
            ('rag_retriever', 'planner'),
            ('supervisor', 'presentation_node'),
        ]

        # Self-correction/retry edges
        retry_edges = [
            ('verifier', 'supervisor'),
            ('executor', 'supervisor'),
            ('supervisor', 'codegen'),
        ]

        G.add_edges_from(primary_edges + conditional_edges + retry_edges)
        return G

    def _get_node_size_list(self, G) -> list:
        """Generate node size list matching graph node order."""
        return [self.node_sizes[node] for node in G.nodes()]

    def draw_graph(self, figsize=(32, 28)) -> plt.Figure:
        """
        Draw professional-grade architecture diagram with enhanced styling,
        clear visual hierarchy, and optimized readability.
        """
        G = self.create_graph()
        pos = self.node_positions

        # Create figure with white background and larger size
        fig, ax = plt.subplots(figsize=figsize, facecolor='white', dpi=150)

        # Professional title styling with MASSIVE font
        ax.text(0, 11, 'OCI Copilot Agent Architecture',
                ha='center', va='center',
                fontsize=42, fontweight='bold',
                family='sans-serif',
                bbox=dict(boxstyle='round,pad=1.0', facecolor='white',
                          edgecolor='#2C3E50', linewidth=4))

        # Draw concentric circles for visual depth with larger radii
        for radius in [4, 7.5]:
            circle = plt.Circle((0, 0), radius, color='#ECF0F1',
                                fill=False, linewidth=2, linestyle=':', alpha=0.4)
            ax.add_patch(circle)

        # Get ordered node size list for edge rendering
        node_size_list = self._get_node_size_list(G)

        # Draw nodes by shape with enhanced styling
        for shape in set(self.node_shapes.values()):
            node_list = [node for node,
                         s in self.node_shapes.items() if s == shape]
            node_sizes_for_shape = [self.node_sizes[n] for n in node_list]

            nx.draw_networkx_nodes(
                G, pos,
                nodelist=node_list,
                node_shape=shape,
                node_color=[self.node_colors[n] for n in node_list],
                node_size=node_sizes_for_shape,
                alpha=0.95,
                edgecolors='black',
                linewidths=3.5,  # Thicker node borders
                ax=ax
            )

        # Define edge styles
        primary_edges = [
            ('start', 'memory_context'),
            ('memory_context', 'supervisor'), ('supervisor', 'normalizer'),
            ('normalizer', 'rag_retriever'), ('normalizer', 'planner'),
            ('rag_retriever', 'presentation_node'), ('planner', 'codegen'),
            ('codegen', 'verifier'), ('verifier', 'executor'),
            ('executor', 'presentation_node'), ('presentation_node', 'memory_manager'),
            ('memory_manager', 'end')
        ]

        conditional_edges = [
            ('rag_retriever', 'planner'),
            ('supervisor', 'presentation_node')
        ]

        retry_edges_curved = [
            ('verifier', 'supervisor'),
            ('executor', 'supervisor'),
            ('supervisor', 'codegen')
        ]

        # Draw primary flow edges (solid black) - edges stop at node boundaries
        nx.draw_networkx_edges(
            G, pos,
            edgelist=primary_edges,
            width=4.0,  # Thicker edges
            edge_color='#2C3E50',
            arrowsize=35,
            arrowstyle='-|>',
            node_size=node_size_list,
            nodelist=list(G.nodes()),
            node_shape='o',
            ax=ax
        )

        # Draw conditional edges (dashed orange) - edges stop at node boundaries
        nx.draw_networkx_edges(
            G, pos,
            edgelist=conditional_edges,
            width=3.5,  # Thicker edges
            style='dashed',
            edge_color='#E67E22',
            arrowsize=30,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.25',
            node_size=node_size_list,
            nodelist=list(G.nodes()),
            node_shape='o',
            ax=ax
        )

        # Draw retry loop edges with distinct curvature (dotted red)
        for i, edge in enumerate(retry_edges_curved):
            rad_values = [0.6, -0.6, 0.3]
            nx.draw_networkx_edges(
                G, pos,
                edgelist=[edge],
                width=3.5,  # Thicker edges
                style='dotted',
                edge_color='#C0392B',
                arrowsize=30,
                arrowstyle='-|>',
                connectionstyle=f'arc3,rad={rad_values[i]}',
                node_size=node_size_list,
                nodelist=list(G.nodes()),
                node_shape='o',
                ax=ax
            )

        # Draw labels with MASSIVE font for maximum readability
        nx.draw_networkx_labels(
            G, pos,
            self.node_labels,
            font_size=20,  # MUCH larger font
            font_weight='bold',
            font_family='sans-serif',
            verticalalignment='center',
            ax=ax
        )

        # Professional legend with better organization and larger elements
        legend_elements = [
            plt.Line2D([0], [0], color='#2C3E50', linewidth=4,
                       label='Conditional / Fallwak Flow'),
            plt.Line2D([0], [0], color='#E67E22', linewidth=3.5,
                       linestyle='--', label='Conditional / Fallback Flow'),
            plt.Line2D([0], [0], color='#C0392B', linewidth=3.5,
                       linestyle=':', label='Processing / Routing Node'),
            plt.Line2D([0], [0], marker='d', color='w',
                       label='Processing / Routing Node',
                       markerfacecolor='#9B59B6', markersize=16,
                       markeredgecolor='black', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w',
                       label='Processing / Routing Node',
                       markerfacecolor='#48C9B0', markersize=16,
                       markeredgecolor='black', markeredgewidth=2),
            plt.Line2D([0], [0], marker='s', color='w',
                       label='Sequential Task Node',
                       markerfacecolor='#F4D03F', markersize=16,
                       markeredgecolor='black', markeredgewidth=2)
        ]

        legend = ax.legend(
            handles=legend_elements,
            loc='upper right',
            fontsize=16,  # MUCH larger legend font
            title="Legend",
            title_fontsize=18,
            frameon=True,
            fancybox=True,
            shadow=True,
            framealpha=0.95,
            edgecolor='#2C3E50',
            facecolor='white'
        )
        legend.get_frame().set_linewidth(2.5)

        # Set axis limits with more padding for larger display
        ax.set_xlim(-10, 10)
        ax.set_ylim(-11, 12.5)
        ax.set_aspect('equal')
        ax.axis('off')

        plt.tight_layout(pad=2)
        return fig

    def save_graph(self, filename: str = 'oci_agent_architecture.png', dpi: int = 300):
        """Save the graph to a high-resolution file."""
        fig = self.draw_graph()
        fig.savefig(filename, dpi=dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        return filename
