# app.py (DEFINITIVE, COMPLETE, WITH GRAPH VISUALIZATION)

import streamlit as st
import os
import time
import pandas as pd
import oci
import json
from dotenv import load_dotenv
from core.graph import build_graph
from core.state import AgentState
from core.llm_manager import call_llm
import uuid

# Graph visualization imports
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    GRAPH_VIZ_AVAILABLE = True
except ImportError:
    GRAPH_VIZ_AVAILABLE = False
    print("⚠️ Graph visualization disabled - install networkx and matplotlib")

# RAG imports (conditional - only when RAG is enabled)
# from rag.tenancy_scanner import master_tenancy_scan
# from rag.embeddings import get_embedding
# from rag.vectorstore import get_chroma_client, add_to_store
from oci_ops.clients import build_config
from core.langsmith import status_badge
from typing import List, Dict, Any, Optional

# ==============================================================================
# UI HELPER FUNCTIONS (MERGED)
# ==============================================================================


def test_api_connection(provider):
    """Test API connection for the selected provider."""
    import time
    start_time = time.time()

    try:
        test_messages = [
            {"role": "user", "content": "Hello, this is a test message. Please respond with 'API test successful'."}
        ]

        if provider == "gemini":
            from core.llm_manager import _call_gemini
            response = _call_gemini(test_messages)
        elif provider == "openai":
            from core.llm_manager import _call_openai
            response = _call_openai(test_messages)
        elif provider == "anthropic":
            from core.llm_manager import _call_anthropic
            response = _call_anthropic(test_messages)
        elif provider == "groq":
            from core.llm_manager import _call_groq
            response = _call_groq(test_messages)
        else:
            return {"success": False, "error": f"Unknown provider: {provider}"}

        response_time = time.time() - start_time
        return {"success": True, "response_time": response_time, "response": response}

    except Exception as e:
        return {"success": False, "error": str(e)}


def init_session():
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(hash(time.time()))


def perform_master_scan(state):
    """
    Perform enhanced master tenancy scan using the new RAG system.
    """
    # Only perform scan if RAG is enabled
    if not st.session_state.get('use_rag_chain', False):
        st.sidebar.warning(
            "⚠️ RAG is disabled. Enable RAG toggle to use tenancy scanning.")
        return

    st.sidebar.info("🔍 Starting Enhanced Master Tenancy Scan...")
    st.sidebar.info(
        "📊 Scanning ALL compartments with improved data quality...")

    try:
        # Import RAG functions only when needed
        from rag.tenancy_scanner import master_tenancy_scan
        # Run master tenancy scan
        scan_result = master_tenancy_scan(state)

        # Display summary
        st.sidebar.success("✅ Master scan completed!")
        st.sidebar.info(
            f"📊 Indexed resources: {scan_result.get('indexed_resources', 0)}")
        st.sidebar.info(
            f"Identity documents: {scan_result.get('identity_docs', 0)}")
        st.sidebar.info(
            f"Compartment documents: {scan_result.get('compartment_docs', 0)}")
        st.sidebar.info(
            f"Compartments scanned: {scan_result.get('compartments_scanned', 0)}")
        st.sidebar.info(
            f"🕒 Scan completed at: {scan_result.get('timestamp', 'N/A')}")

    except Exception as e:
        st.sidebar.error(f"❌ Master scan failed: {str(e)}")
        print(f"❌ Master scan error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    if "last_response" not in st.session_state:
        st.session_state.last_response = None


def append_chat(role, text):
    st.session_state['chat_history'].append((role, text))


def render_chat_history():
    chat_history = st.session_state.get('chat_history', [])

    # Show simple welcome message if no chat history
    if not chat_history:
        with st.chat_message("🤖"):
            st.markdown("""
<div style="text-align: center; padding: 20px;">
<h1>Welcome!!</h1>
</div>
            """, unsafe_allow_html=True)
    else:
        for sender, message in chat_history:
            st.chat_message("🧑" if sender == 'user' else "🤖").markdown(message)


def render_table(items: List[Dict[str, Any]], title: Optional[str] = None, preferred_cols: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    if not items:
        return None
    try:
        df = pd.DataFrame(items)
        cols_to_display = []
        if preferred_cols:
            cols_to_display = [
                col for col in preferred_cols if col in df.columns]

        if not cols_to_display:
            default_order = ["display_name", "name",
                             "id", "lifecycle_state", "shape"]
            available_columns = list(df.columns)
            cols_to_display = [
                col for col in default_order if col in available_columns]
            for col in available_columns:
                if col not in cols_to_display:
                    cols_to_display.append(col)
            # Show ALL columns, no limit
        if not cols_to_display and available_columns:
            cols_to_display = available_columns  # Show ALL columns

        st.dataframe(df[cols_to_display], width='stretch')
        column_names_str = [str(c) for c in cols_to_display]
        st.caption(
            f"Showing {len(df)} rows. Displaying {len(cols_to_display)} columns: {', '.join(column_names_str)}")
        return df[cols_to_display]
    except Exception as e:
        st.error(f"Error rendering table: {e}")
        return None


def download_buttons(df: pd.DataFrame, base_name: str = "oci_export"):
    import datetime
    import io
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("⬇️ CSV", data=df.to_csv(index=False).encode(
            "utf-8"), file_name=f"{base_name}_{ts}.csv", mime="text/csv")
    with c2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='data')
        st.download_button("⬇️ XLSX", data=output.getvalue(
        ), file_name=f"{base_name}_{ts}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c3:
        try:
            # Convert DataFrame to dict and handle non-serializable objects
            data_dict = df.to_dict(orient="records")
            # Use default=str to handle non-serializable objects
            json_string = json.dumps(data_dict, indent=2, default=str)
            st.download_button("⬇️ JSON", data=json_string,
                               file_name=f"{base_name}_{ts}.json", mime="application/json")
        except Exception as e:
            st.error(f"JSON export failed: {str(e)}")
            # Fallback: convert all values to strings
            safe_dict = []
            for record in df.to_dict(orient="records"):
                safe_record = {k: str(v) for k, v in record.items()}
                safe_dict.append(safe_record)
            json_string = json.dumps(safe_dict, indent=2)
            st.download_button("⬇️ JSON (Safe)", data=json_string,
                               file_name=f"{base_name}_{ts}_safe.json", mime="application/json")

# ==============================================================================
# GRAPH VISUALIZATION FUNCTION
# ==============================================================================


def draw_graph_matplotlib(agent_graph):
    """Takes a compiled LangGraph agent and draws it using networkx and matplotlib."""
    if not GRAPH_VIZ_AVAILABLE:
        st.warning(
            "⚠️ Graph visualization requires networkx and matplotlib. Install them to see the workflow graph.")
        return

    try:
        graph = agent_graph.get_graph()
        nx_graph = nx.DiGraph()
        for node_name in graph.nodes:
            nx_graph.add_node(node_name)
        for edge in graph.edges:
            nx_graph.add_edge(edge.source, edge.target)

        fig, ax = plt.subplots(figsize=(12, 10))
        pos = nx.kamada_kawai_layout(nx_graph)
        nx.draw_networkx_nodes(nx_graph, pos, node_size=3500,
                               node_color="#a7c7e7", ax=ax)
        nx.draw_networkx_labels(nx_graph, pos, font_size=9,
                                font_weight="bold", ax=ax)
        nx.draw_networkx_edges(nx_graph, pos, width=1.0, alpha=0.6,
                               edge_color="gray", arrows=True, arrowsize=20, ax=ax)
        ax.set_title("Agent State Graph", size=16)
        plt.tight_layout()
        plt.axis("off")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"❌ Error drawing graph: {e}")

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================


# --- Initialization ---
load_dotenv(dotenv_path='.env', override=True)
st.set_page_config(page_title="CloudAgentra", layout="wide")
st.title("☁️ CloudAgentra")

init_session()
if "agent_graph" not in st.session_state:
    st.session_state.agent_graph = build_graph()

# --- OCI Namespace Helper ---


def fetch_namespace(cfg):
    try:
        client = oci.object_storage.ObjectStorageClient(cfg)
        response = client.get_namespace()
        return response.data if response and hasattr(response, 'data') else None
    except Exception:
        return None


# --- Sidebar ---
with st.sidebar:
    st.header("☁️ CloudAgentra")
    st.caption("Your Cloud Assistant")
    # Collapsible LLM Configuration Section
    with st.expander("🤖 LLM Configuration", expanded=True):
        # Dynamic LLM Provider Selection
        provider_map = {
            "Google (Gemini 2.5 Pro)": "gemini",
            "OpenAI (GPT-4)": "openai",
            "Groq (Llama 3)": "groq",
            "Anthropic (Claude)": "anthropic"
        }

        display_name = st.selectbox(
            "Select LLM Provider", provider_map.keys(), index=0)
        selected_provider = provider_map[display_name]

        st.session_state['llm_preference'] = {
            "provider": selected_provider}

        # Dynamic API Key Input based on selected provider
        if selected_provider == "gemini":
            api_key = st.text_input(
                "Google API Key",
                value=os.getenv('GOOGLE_API_KEY', '') or os.getenv(
                    'GEMINI_API_KEY', ''),
                type="password",
                help="Get your API key from Google AI Studio"
            )
            if api_key:
                os.environ['GOOGLE_API_KEY'] = api_key

        elif selected_provider == "openai":
            api_key = st.text_input(
                "OpenAI API Key",
                value=os.getenv('OPENAI_API_KEY', ''),
                type="password",
                help="Get your API key from OpenAI Platform"
            )
            if api_key:
                os.environ['OPENAI_API_KEY'] = api_key

        elif selected_provider == "groq":
            api_key = st.text_input(
                "Groq API Key",
                value=os.getenv('GROQ_API_KEY', ''),
                type="password",
                help="Get your API key from Groq Console"
            )
            if api_key:
                os.environ['GROQ_API_KEY'] = api_key

        elif selected_provider == "anthropic":
            api_key = st.text_input(
                "Anthropic API Key",
                value=os.getenv('ANTHROPIC_API_KEY', ''),
                type="password",
                help="Get your API key from Anthropic Console"
            )
            if api_key:
                os.environ['ANTHROPIC_API_KEY'] = api_key

        # API Test Section
        if st.button("🧪 Test API Connection"):
            test_result = test_api_connection(selected_provider)
            if test_result["success"]:
                st.success(f"✅ {selected_provider.upper()} API working!")
                st.info(f"Response time: {test_result['response_time']:.2f}s")
            else:
                st.error(
                    f"❌ {selected_provider.upper()} API failed: {test_result['error']}")

    st.divider()
    # Collapsible OCI Configuration Section
    with st.expander("☁️ OCI Cloud Configuration", expanded=False):
        show_creds = st.checkbox("Show OCI creds", value=False)
        try:
            defaults = build_config({})
        except Exception:
            defaults = {}

        oci_creds = {
            'tenancy': st.text_input("Tenancy OCID", value=defaults.get('tenancy') or os.getenv('OCI_TENANCY', ''), type="default" if show_creds else "password"),
            'user': st.text_input("User OCID", value=defaults.get('user') or os.getenv('OCI_USER', ''), type="default" if show_creds else "password"),
            'fingerprint': st.text_input("Key Fingerprint", value=defaults.get('fingerprint') or os.getenv('OCI_FINGERPRINT', ''), type="default" if show_creds else "password"),
            'region': st.text_input("Region", value=defaults.get('region') or os.getenv('OCI_REGION', 'ap-mumbai-1'))
        }

        # Auto-fill private key from .oci folder or environment
        default_key = ""
        # Try to read from .oci/config file first
        try:
            oci_config_path = os.path.expanduser("~/.oci/config")
            if os.path.exists(oci_config_path):
                import configparser
                config = configparser.ConfigParser()
                config.read(oci_config_path)
                if 'DEFAULT' in config and 'key_file' in config['DEFAULT']:
                    key_file_path = config['DEFAULT']['key_file']
                    if os.path.exists(key_file_path):
                        with open(key_file_path, 'r') as f:
                            default_key = f.read()
        except:
            pass

        # Fallback to environment variables
        if not default_key:
            default_key = os.getenv('OCI_PRIVATE_KEY', '') or os.getenv(
                'OCI_KEY_CONTENT', '')

        oci_creds['key_content'] = st.text_area("Paste Private Key Content",
                                                value=default_key,
                                                height=150,
                                                help="Paste your entire private key including -----BEGIN RSA PRIVATE KEY----- and -----END RSA PRIVATE KEY-----")

        # Test OCI Connection
        if st.button("🧪 Test OCI Connection"):
            try:
                namespace = fetch_namespace(oci_creds)
                if namespace:
                    st.success("✅ OCI Connection Successful!")
                    st.info(f"Namespace: {namespace}")
                    st.session_state['oci_creds'] = oci_creds
                    st.session_state['oci_creds']['namespace'] = namespace
                else:
                    st.error("❌ OCI Connection Failed - Check credentials")
            except Exception as e:
                st.error(f"❌ OCI Connection Error: {str(e)}")
        else:
            st.session_state['oci_creds'] = oci_creds
            namespace = fetch_namespace(st.session_state['oci_creds'])
            if namespace:
                st.session_state['oci_creds']['namespace'] = namespace

    st.divider()
    # Chain Routing Section
    with st.expander("🔄 Chain Routing", expanded=False):
        # Toggle for RAG vs Planner chain
        use_rag_chain = st.toggle(
            "🧠 Use RAG Chain",
            value=False,
            help="Toggle between RAG chain (for cached data) and Planner chain (for live execution)"
        )

        # Store the toggle state in session
        st.session_state['use_rag_chain'] = use_rag_chain

        if use_rag_chain:
            st.info("🧠 **RAG Chain Active** - Queries will use cached data")
        else:
            st.info(
                "⚙️ **Planner Chain Active** - Queries will execute live OCI operations")

    st.divider()
    # Tools Section
    with st.expander("🛠️ Tools", expanded=False):
        # Master Tenancy Scan Button
        if st.button("🔍 Scan Master Tenancy"):
            if st.session_state.get('oci_creds'):
                # Create a state object for the scan with LLM preferences
                scan_state = {
                    'oci_creds': st.session_state['oci_creds'],
                    'session_id': st.session_state.get('session_id', 'unknown'),
                    'llm_preference': st.session_state.get('llm_preference', {"provider": "openai"}),
                    'call_llm': call_llm
                }
                perform_master_scan(scan_state)
            else:
                st.error("❌ Please configure OCI credentials first!")

    # Add divider between Tools and RAG
    st.divider()

    # Collapsible RAG Status Section
    with st.expander("RAG", expanded=False):
        # Show enhanced vector store status
        try:
            # Only import and initialize RAG when RAG is enabled
            if st.session_state.get('use_rag_chain', False):
                from rag.vectorstore import get_vector_store
                vector_store = get_vector_store()
                stats = vector_store.get_collection_stats()
            else:
                st.info(
                    "💡 RAG is disabled. Enable RAG toggle to use vector store features.")
                stats = {"status": "disabled"}

            if stats.get("status") == "disabled":
                # RAG is disabled, show appropriate message
                pass
            elif "error" in stats:
                st.warning(f"⚠️ Vector Store: Error - {stats['error']}")
                st.info(
                    "💡 Try running 'Scan Master Tenancy' to initialize the vector store")
            else:
                st.info(
                    f"📚 Enhanced Vector Store: {stats.get('total_documents', 0)} documents")
                st.info(f"🔧 Services: {len(stats.get('services', []))}")
                st.info(
                    f"📁 Compartments: {len(stats.get('compartments', []))}")
                st.info(
                    f"🔢 Total Resources: {stats.get('total_resources', 0)}")

                # Show services
                services = stats.get('services', [])
                if services:
                    st.info(f"🔧 Available: {', '.join(services[:3])}")
                    if len(services) > 3:
                        st.info(f"🔧 ... and {len(services) - 3} more")
        except Exception as e:
            st.warning(f"⚠️ Enhanced Vector Store: Error - {str(e)}")
            st.info(
                "💡 Try running 'Scan Master Tenancy' to initialize the vector store")

        st.divider()

        # RAG System initialization button
        if st.button("🔧 Initialize RAG System"):
            try:
                from rag.init_rag import initialize_rag_system, check_rag_health

                with st.spinner("Initializing RAG system..."):
                    init_results = initialize_rag_system()

                if init_results["success"]:
                    st.success("✅ RAG System initialized successfully!")
                    st.info(
                        f"📊 Completed {len(init_results['steps_completed'])} steps")
                    if init_results.get("warnings"):
                        st.warning("⚠️ Warnings:")
                        for warning in init_results["warnings"][:2]:
                            st.info(f"   • {warning}")
                else:
                    st.error("❌ RAG System initialization failed!")
                    # Show first 2 errors
                    for error in init_results["errors"][:2]:
                        st.error(f"   • {error}")

                # Check health after initialization
                health_results = check_rag_health()
                if health_results["healthy"]:
                    st.success("🏥 RAG System is healthy!")
                else:
                    st.warning("⚠️ RAG System has issues")
                    # Show first 2 issues
                    for issue in health_results["issues"][:2]:
                        st.warning(f"   • {issue}")

                # Show recommendations
                if health_results.get("recommendations"):
                    st.info("💡 Recommendations:")
                    for rec in health_results["recommendations"][:2]:
                        st.info(f"   • {rec}")

            except Exception as e:
                st.error(f"❌ RAG initialization failed: {str(e)}")

        # Enhanced RAG testing button
        if st.button("🧪 Test Enhanced RAG"):
            try:
                from rag.test_rag import run_comprehensive_rag_tests

                with st.spinner("Running comprehensive RAG tests..."):
                    test_results = run_comprehensive_rag_tests()

                summary = test_results.get('overall_summary', {})
                success_rate = summary.get('success_rate', 0)

                if success_rate >= 0.8:
                    st.success(f"✅ RAG Tests Passed: {success_rate:.1%}")
                else:
                    st.warning(
                        f"⚠️ RAG Tests: {success_rate:.1%} success rate")

                st.info(
                    f"📊 Tests: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} passed")

                # Show recommendations
                if test_results.get('recommendations'):
                    st.info("💡 Recommendations:")
                    for rec in test_results["recommendations"][:2]:
                        st.info(f"   • {rec}")

            except Exception as e:
                st.error(f"❌ RAG Testing failed: {str(e)}")

        if st.button("🗑️ Clear Enhanced Vector Store"):
            try:
                from rag.vectorstore import get_vector_store
                vector_store = get_vector_store()
                vector_store.clear_all_collections()
                st.success("✅ Enhanced Vector Store cleared!")
                st.info("💡 Run 'Initialize RAG System' to rebuild")
            except Exception as e:
                st.error(f"❌ Clear failed: {str(e)}")

    # Add divider between RAG and Clear Chat History
    st.divider()

    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.session_state.last_response = None
        st.rerun()
    st.sidebar.caption(status_badge())

    st.divider()
    st.header("📊 Performance Metrics")

    # Show execution strategy and performance
    execution_strategy = st.session_state.get('execution_strategy', 'unknown')
    if execution_strategy != 'unknown':
        strategy_emoji = {
            'direct_fetch': '⚡',
            'multi_step': '🔧',
            'llm_fallback': '🤖'
        }

        st.metric(
            label="Execution Strategy",
            value=f"{strategy_emoji.get(execution_strategy, '❓')} {execution_strategy.replace('_', ' ').title()}"
        )

        # Show node timing if available
        node_status = st.session_state.get('node_status', {})
        if node_status:
            total_time = sum(data.get('time', 0) for data in node_status.values(
            ) if data.get('status') == 'completed')
            if total_time > 0:
                st.metric(
                    label="Total Execution Time",
                    value=f"{total_time:.1f}s"
                )

                # Show breakdown
                with st.expander("📈 Node Performance Breakdown"):
                    for node, data in node_status.items():
                        if data.get('status') == 'completed':
                            st.write(f"✅ {node}: {data.get('time', 0):.1f}s")

    st.divider()
    st.header("📊 Agent Internals")

    # Enhanced flowchart visualization
    if st.checkbox("Show Enhanced Flowchart"):
        try:
            from core.graph_visualizer import draw_agent_flowchart
            draw_agent_flowchart()
        except Exception as e:
            st.error(f"Failed to load flowchart: {e}")
            st.info("Falling back to standard graph visualization...")
            agent_graph = st.session_state.get("agent_graph")
            if agent_graph:
                draw_graph_matplotlib(agent_graph)
            else:
                st.warning("Agent graph not available.")

# ============================================================================
# AMAZON Q STYLE PROGRESS DISPLAY
# ============================================================================


def _update_progress_display(placeholder, current_node):
    """Update the progress display with Streamlit spinner for current node."""
    node_status = st.session_state.get('node_status', {})

    # Get execution strategy from state
    execution_strategy = st.session_state.get('execution_strategy', 'unknown')
    print(f"DEBUG: Current execution strategy: {execution_strategy}")

    # If strategy is unknown, try to infer from current node
    if execution_strategy == 'unknown':
        if current_node == 'planner':
            execution_strategy = 'analyzing'
        elif current_node == 'codegen':
            execution_strategy = 'multi_step'
        elif current_node == 'executor':
            execution_strategy = 'executing'
        else:
            execution_strategy = 'processing'
    strategy_emoji = {
        'direct_fetch': '⚡',
        'multi_step': '🔧',
        'llm_fallback': '🤖',
        'analyzing': '🔍',
        'executing': '⚙️',
        'processing': '🔄',
        'unknown': '❓'
    }

    # Node display names and icons - Show process instead of model names
    node_info = {
        'normalizer': ('Normalizing query', 'Processing'),
        'planner': ('Planning operations', 'Processing'),
        'codegen': ('Generating code', 'Processing'),
        'verifier': ('Verifying safety', 'Processing'),
        'executor': ('Executing operations', 'Processing'),
        'presentation_node': ('Preparing results', 'Processing'),
        'rag_retriever': ('Retrieving from cache', 'Processing')
    }

    # Only show RAG-related progress if RAG is enabled
    use_rag_chain = st.session_state.get('use_rag_chain', False)
    if not use_rag_chain:
        # Remove RAG-related entries when RAG is disabled
        node_info = {k: v for k, v in node_info.items() if k !=
                     'rag_retriever'}

    # Get current node info for spinner
    current_label, current_model = node_info.get(
        current_node, ('Processing', 'N/A'))

    # Show spinner for the current node that's actually running
    if current_node in node_info:
        current_label, current_model = node_info[current_node]
        with st.spinner(f"🔄 {current_label}..."):
            # Build progress display
            total_time = 0
            display_text = "```\n🤖 Processing Your Request\n" + "="*60 + "\n"
            display_text += f"{strategy_emoji.get(execution_strategy, '❓')} Strategy: {execution_strategy.replace('_', ' ').title()}\n"
            display_text += "="*60 + "\n\n"

            for node, (label, model) in node_info.items():
                status_data = node_status.get(node, {})

                if status_data.get('status') == 'completed':
                    elapsed = status_data.get('time', 0)
                    total_time += elapsed
                    display_text += f"✅ {label:<30} {elapsed:>6.1f}s\n"
                elif node == current_node:
                    display_text += f"🔄 {label:<30} {'running':>6}\n"
                else:
                    display_text += f"⏳ {label:<30} {'pending':>6}\n"

            display_text += "\n" + "="*60
            display_text += f"\n⏱️  Total: {total_time:.1f}s\n```"

            # Update placeholder
            placeholder.markdown(display_text)
    else:
        # Fallback if no current node
        total_time = 0
        display_text = "```\n🤖 Processing Your Request\n" + "="*60 + "\n"
        display_text += f"{strategy_emoji.get(execution_strategy, '❓')} Strategy: {execution_strategy.replace('_', ' ').title()}\n"
        display_text += "="*60 + "\n\n"

        for node, (label, model) in node_info.items():
            status_data = node_status.get(node, {})

            if status_data.get('status') == 'completed':
                elapsed = status_data.get('time', 0)
                total_time += elapsed
                display_text += f"✅ {label:<30} {elapsed:>6.1f}s\n"
            else:
                display_text += f"⏳ {label:<30} {'pending':>6}\n"

        display_text += "\n" + "="*60
        display_text += f"\n⏱️  Total: {total_time:.1f}s\n```"

        # Update placeholder
        placeholder.markdown(display_text)


# --- Main Chat Logic ---
render_chat_history()
if st.session_state.get("last_response"):
    presentation_object = st.session_state.last_response or {}
    table_data = presentation_object.get("data", [])
    output_format = presentation_object.get("format", "chat")
    preferred_columns = presentation_object.get("columns", [])
    if output_format == "table" and table_data:
        df = render_table(table_data, title="Results",
                          preferred_cols=preferred_columns)
        if df is not None and not df.empty:
            download_buttons(df)
    st.session_state.last_response = None

if prompt := st.chat_input("Ask CloudAgentra..."):
    append_chat("user", prompt)
    st.rerun()

if st.session_state.chat_history and st.session_state.chat_history[-1][0] == 'user':
    user_input = st.session_state.chat_history[-1][1]

    # Check if this is a confirmation response
    if st.session_state.get('confirmation_required'):
        # Handle confirmation response
        st.session_state['confirmation_response'] = user_input
        st.session_state['confirmation_required'] = False
        # Continue with the graph execution
    elif st.session_state.get('parameter_gathering_required') or st.session_state.get('compartment_selection_required'):
        # Handle parameter selection response
        st.session_state['parameter_selection_response'] = user_input
        st.session_state['parameter_gathering_required'] = False
        st.session_state['compartment_selection_required'] = False
        # Continue with the graph execution
    else:
        # Reset previous response when new query is submitted
        if 'last_response' in st.session_state:
            del st.session_state['last_response']
        if 'node_status' in st.session_state:
            st.session_state['node_status'] = {}

    with st.chat_message("assistant"):
        # Initialize node status tracking
        if 'node_status' not in st.session_state:
            st.session_state.node_status = {}

        # Create progress container
        progress_placeholder = st.empty()

        # Show initial progress immediately
        progress_placeholder.markdown(
            "```\n🤖 Processing Your Request\n" + "="*60 + "\n⏳ Initializing...\n" + "="*60 + "\n```")

        with st.spinner("Processing..."):
            initial_state: AgentState = {
                "user_input": user_input,
                "session_id": st.session_state.session_id,
                "oci_creds": st.session_state.get('oci_creds', {}),
                "llm_preference": st.session_state.get('llm_preference', {}),
                "call_llm": call_llm,
                "db_path": ".oci_agent.sqlite",
                "chat_history": [msg for role, msg in st.session_state.chat_history],
                # Add toggle state
                "use_rag_chain": st.session_state.get('use_rag_chain', False),
                "plan": None,
                "plan_error": None,
                "plan_valid": False,
                "verify_retries": 0,
                "rag_found": False,
                "rag_result": [],
                "rag_metadata": [],
                "feedback": None,
                # Add confirmation state
                "confirmation_required": st.session_state.get('confirmation_required', False),
                "confirmation_response": st.session_state.get('confirmation_response'),
                "pending_plan": st.session_state.get('pending_plan'),
                # Add parameter gathering state
                "parameter_gathering_required": st.session_state.get('parameter_gathering_required', False),
                "parameter_selection_response": st.session_state.get('parameter_selection_response'),
                "compartment_selection_required": st.session_state.get('compartment_selection_required', False),
                "compartment_data": st.session_state.get('compartment_data', []),
            }

            final_state = {}
            presentation_object = {}
            try:
                # ✅ FIXED: Merge updates instead of overwriting
                for chunk in st.session_state.agent_graph.stream(initial_state, {"recursion_limit": 50}):
                    for node_name, update in chunk.items():
                        final_state.update(update)

                        # Handle confirmation states
                        if 'confirmation_required' in update:
                            st.session_state['confirmation_required'] = update['confirmation_required']
                        if 'pending_plan' in update:
                            st.session_state['pending_plan'] = update['pending_plan']
                        if 'action_cancelled' in update:
                            st.session_state['action_cancelled'] = update['action_cancelled']

                        # Track execution strategy for performance metrics
                        if 'execution_strategy' in update:
                            st.session_state['execution_strategy'] = update['execution_strategy']
                            print(
                                f"📊 Execution Strategy: {update['execution_strategy']}")

                        # Update progress display
                        current_node = update.get('last_node', node_name)
                        if current_node:
                            _update_progress_display(
                                progress_placeholder, current_node)

                        # Debug: show state evolution
                        print(f"DEBUG: Updated state → {final_state}\n")

                if final_state.get("presentation"):
                    presentation_object = final_state.get("presentation")
                elif final_state.get("general_chat"):
                    presentation_object = {"summary": final_state.get(
                        "general_chat"), "format": "chat", "data": []}
                else:
                    presentation_object = {
                        "summary": "Process complete.", "format": "chat", "data": []}
            except Exception as e:
                presentation_object = {
                    "summary": f"A critical error occurred: {e}", "format": "error", "data": []}

            # REMOVED: Human-in-the-loop confirmation for full autonomy
            # All operations now run automatically without user confirmation

            # Present results directly
            summary_text = (presentation_object or {}).get(
                "summary", "No summary available.")
            append_chat("assistant", summary_text)
            st.session_state.last_response = presentation_object

            # Display execution timing if available
            planning_time = final_state.get("planning_time")
            if planning_time:
                st.info(f"⏱️ Planning completed in {planning_time:.2f}s")

            st.rerun()
