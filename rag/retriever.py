# rag/retriever.py - Enhanced Version with LLM-powered pre-search filtering

from rag.embeddings import get_embedding_manager
from rag.vectorstore import get_vector_store
from core.state import AgentState # Need state for LLM calls
from core.llm_manager import call_llm as default_call_llm
from typing import List, Dict, Any, Optional, Tuple
import re
import json

class EnhancedRetriever:
    """Enhanced retriever with LLM-powered pre-search filtering."""

    def __init__(self):
        self.embedding_manager = get_embedding_manager()
        self.vector_store = get_vector_store()
        self.intent_resource_map = {
            "list users": ["identity.list_users"],
            "list groups": ["identity.list_groups"],
            "list policies": ["identity.list_policies"],
            "list instances": ["compute.list_instances"],
            "list volumes": ["blockstorage.list_volumes", "blockstorage.list_boot_volumes"],
            "list buckets": ["objectstorage.list_buckets"],
            "list vcns": ["virtualnetwork.list_vcns"],
            "list subnets": ["virtualnetwork.list_subnets"],
            "list security lists": ["virtualnetwork.list_security_lists"],
            "list route tables": ["virtualnetwork.list_route_tables"],
            "list load balancers": ["loadbalancer.list_load_balancers"],
        }

    def _get_intent_filter(self, query: str, state: AgentState) -> Optional[Dict[str, Any]]:
        """Use an LLM to determine the user's intent and create a precise metadata filter."""
        try:
            print("--- RETRIEVER: Getting intent filter via LLM ---")
            call_llm_func = state.get("call_llm", default_call_llm)
            possible_intents = list(self.intent_resource_map.keys())
            
            prompt = f'''Given the user's query, find the single best matching intent from the provided list.
Respond with ONLY the string of the best matching intent. For example: 'list instances'.
If no clear match is found, respond with "None".

User Query: "{query}"

Possible Intents:
{json.dumps(possible_intents, indent=2)}
'''
            messages = [
                {"role": "system", "content": "You are an expert at matching user queries to predefined intents."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = call_llm_func(state, messages, 'retriever_intent_matcher')
            matched_intent = llm_response.strip().lower().replace('"' , '')

            if matched_intent == "none":
                print("DEBUG: LLM could not determine a specific intent.")
                return None

            print(f"DEBUG: LLM matched intent: '{matched_intent}'")
            target_operations = self.intent_resource_map.get(matched_intent, [])

            if not target_operations:
                return None

            # Create a filter based on the identified operations
            if len(target_operations) == 1:
                service, operation = target_operations[0].split('.')
                return {"$and": [{"service": service}, {"operation": operation}]}
            else:
                or_conditions = []
                for op_str in target_operations:
                    service, operation = op_str.split('.')
                    or_conditions.append({"$and": [{"service": service}, {"operation": operation}]})
                return {"$or": or_conditions}

        except Exception as e:
            print(f"⚠️ Intent filter error: {e}. Proceeding without pre-filtering.")
            return None

    def retrieve(self, query: str, state: AgentState, top_k: int = 5) -> Dict[str, Any]:
        """
        Enhanced retrieval with LLM-powered pre-search filtering.
        """
        if not query or not query.strip():
            return {"documents": [], "metadatas": [], "rag_found": False}

        print(f"🔍 Enhanced retrieval for query: '{query}'")

        # Get a precise filter from the LLM
        filters = self._get_intent_filter(query, state)
        if filters:
            print(f"🎯 Applying LLM-generated pre-search filter: {filters}")

        # Generate embedding for the original, clean query
        embedding = self.embedding_manager.get_embedding(query)

        # Perform search
        search_results = self.vector_store.search_resources(
            query=query,
            embedding=embedding,
            top_k=top_k,
            filters=filters
        )

        documents = search_results.get("documents", [])
        rag_found = bool(documents)

        print(f"✅ Enhanced retrieval: {len(documents)} results, rag_found: {rag_found}")

        return {
            "documents": documents,
            "metadatas": search_results.get("metadatas", []),
            "rag_found": rag_found,
            "filters_applied": filters
        }

# Global instance
_enhanced_retriever = None

def get_enhanced_retriever() -> EnhancedRetriever:
    """Get global enhanced retriever instance."""
    global _enhanced_retriever
    if _enhanced_retriever is None:
        _enhanced_retriever = EnhancedRetriever()
    return _enhanced_retriever

# The main function called by the graph
def retrieve(state: AgentState) -> Dict[str, Any]:
    """Main retrieval function for the graph.
    The user query is now taken from the state, which is normalized.
    """
    query = state.get("user_input", "")
    retriever = get_enhanced_retriever()
    results = retriever.retrieve(query, state, top_k=5) # Pass state down
    
    # The key for the documents in the state is 'rag_result'
    return {
        "rag_result": results.get("documents"),
        "rag_metadata": results.get("metadatas"),
        "rag_found": results.get("rag_found"),
        "last_node": "rag_retriever"
    }
