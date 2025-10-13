# rag/vectorstore.py - Enhanced Version

import chromadb
from chromadb.config import Settings
import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import hashlib


class EnhancedVectorStore:
    """Enhanced vector store with better metadata, deduplication, and search capabilities."""

    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            persist_directory = os.path.join(
                os.path.dirname(__file__), "chroma_db")

        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "oci_resources_enhanced"
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Get or create enhanced collection with proper metadata schema."""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            print(f"📚 Using existing collection: {self.collection_name}")
        except Exception as e:
            # Handle both ValueError and NotFoundError from ChromaDB
            print(
                f"📚 Collection '{self.collection_name}' not found, creating new one...")
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine",
                          "description": "Enhanced OCI resources with rich metadata"}
            )
            print(f"📚 Created new collection: {self.collection_name}")

        return collection

    def generate_document_id(self, service: str, operation: str, compartment_id: str, resource_id: str = None) -> str:
        """Generate consistent document ID for deduplication."""
        base_id = f"{service}_{operation}_{compartment_id}"
        if resource_id:
            base_id += f"_{resource_id}"
        return hashlib.md5(base_id.encode()).hexdigest()

    def create_rich_metadata(self, service: str, operation: str, compartment: str,
                             compartment_id: str, resource_count: int,
                             resource_data: List[Dict], scan_timestamp: str = None) -> Dict[str, Any]:
        """Create rich metadata for better filtering and search."""
        if scan_timestamp is None:
            scan_timestamp = datetime.now(timezone.utc).isoformat()

        # Extract resource types and states
        resource_types = set()
        lifecycle_states = set()
        resource_names = []

        for resource in resource_data[:10]:  # Analyze first 10 resources
            if isinstance(resource, dict):
                if 'resource_type' in resource:
                    resource_types.add(resource['resource_type'])
                if 'lifecycle_state' in resource:
                    lifecycle_states.add(resource['lifecycle_state'])
                if 'display_name' in resource:
                    resource_names.append(resource['display_name'])
                elif 'name' in resource:
                    resource_names.append(resource['name'])

        return {
            "service": service,
            "operation": operation,
            "compartment": compartment,
            "compartment_id": compartment_id,
            "resource_count": resource_count,
            "resource_types": ",".join([str(rt) for rt in resource_types]),
            "lifecycle_states": ",".join([str(ls) for ls in lifecycle_states]),
            # First 5 names as string
            "resource_names": ",".join([str(name) for name in resource_names[:5]]),
            "scan_timestamp": scan_timestamp,
            "data_version": "2.0",
            "searchable_text": f"{service} {operation} {compartment} {' '.join(resource_names[:3])}"
        }

    def create_searchable_text(self, service: str, operation: str, compartment: str,
                               resource_data: List[Dict]) -> str:
        """Create optimized searchable text for embeddings."""
        # Extract key information for better search
        resource_summaries = []

        for resource in resource_data[:5]:  # Limit to first 5 for performance
            if isinstance(resource, dict):
                summary_parts = []

                # Add key identifiers
                if 'display_name' in resource:
                    summary_parts.append(f"name:{resource['display_name']}")
                elif 'name' in resource:
                    summary_parts.append(f"name:{resource['name']}")

                # Add state information
                if 'lifecycle_state' in resource:
                    summary_parts.append(
                        f"state:{resource['lifecycle_state']}")

                # Add type information
                if 'shape' in resource:
                    summary_parts.append(f"shape:{resource['shape']}")

                if summary_parts:
                    resource_summaries.append(" ".join(summary_parts))

        # Create comprehensive searchable text
        searchable_text = f"""
Service: {service}
Operation: {operation}
Compartment: {compartment}
Resources: {len(resource_data)} items
Summary: {', '.join(resource_summaries)}
        """.strip()

        return searchable_text

    def add_resource_batch(self, resources_data: List[Dict[str, Any]],
                           embeddings: List[List[float]]) -> List[str]:
        """Add multiple resources efficiently with deduplication."""
        documents = []
        metadatas = []
        ids = []

        for i, resource_data in enumerate(resources_data):
            service = resource_data.get('service', 'unknown')
            operation = resource_data.get('operation', 'unknown')
            compartment = resource_data.get('compartment', 'unknown')
            compartment_id = resource_data.get('compartment_id', 'unknown')
            resource_count = resource_data.get('resource_count', 0)

            # Parse resource data
            try:
                if isinstance(resource_data.get('result'), str):
                    # Parse from string format
                    resource_objects = self._parse_resource_string(
                        resource_data['result'])
                else:
                    resource_objects = resource_data.get('resources', [])
            except Exception as e:
                print(f"⚠️ Failed to parse resource data: {e}")
                resource_objects = []

            # Create document ID for deduplication
            doc_id = self.generate_document_id(
                service, operation, compartment_id)

            # Create rich metadata
            metadata = self.create_rich_metadata(
                service, operation, compartment, compartment_id,
                resource_count, resource_objects
            )

            # Create searchable text
            searchable_text = self.create_searchable_text(
                service, operation, compartment, resource_objects
            )

            documents.append(searchable_text)
            metadatas.append(metadata)
            ids.append(doc_id)

        # Add to collection
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids
            )
            print(f"✅ Added {len(documents)} resources to vector store")
            return ids
        except Exception as e:
            print(f"❌ Failed to add resources to vector store: {e}")
            return []

    def _parse_resource_string(self, resource_string: str) -> List[Dict]:
        """Parse resource data from string format."""
        try:
            # Extract JSON part from the string
            import re
            json_match = re.search(
                r'Resources:\s*(\[.*?)(?=\n\n|$)', resource_string, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                # Clean up truncated JSON
                if '...' in json_str:
                    last_complete = json_str.rfind('}')
                    if last_complete > 0:
                        json_str = json_str[:last_complete+1] + ']'

                return json.loads(json_str)
        except Exception as e:
            print(f"⚠️ Failed to parse resource string: {e}")

        return []

    def search_resources(self, query: str, embedding: List[float],
                         top_k: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced search with filtering and better result formatting."""
        try:
            # Perform search
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, self.collection.count()),
                where=filters if filters else None
            )

            # Extract and format results
            documents = results.get("documents", [[]])[
                0] if results.get("documents") else []
            metadatas = results.get("metadatas", [[]])[
                0] if results.get("metadatas") else []
            distances = results.get("distances", [[]])[
                0] if results.get("distances") else []

            # Calculate relevance scores
            relevance_scores = []
            for distance in distances:
                # Convert distance to relevance score (0-1, higher is better)
                relevance_score = max(0, 1 - distance)
                relevance_scores.append(relevance_score)

            print(
                f"🔍 Enhanced search: {len(documents)} results, avg relevance: {sum(relevance_scores)/len(relevance_scores):.3f}" if relevance_scores else "🔍 Enhanced search: 0 results"
            )

            return {
                "documents": documents,
                "metadatas": metadatas,
                "distances": distances,
                "relevance_scores": relevance_scores,
                "total_results": len(documents)
            }

        except Exception as e:
            print(f"❌ Enhanced search failed: {e}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "relevance_scores": [],
                "total_results": 0
            }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get detailed collection statistics."""
        try:
            count = self.collection.count()

            # Get sample of metadata to analyze
            sample_results = self.collection.get(limit=100)
            metadatas = sample_results.get("metadatas", [])

            # Analyze services and compartments
            services = set()
            compartments = set()
            total_resources = 0

            for metadata in metadatas:
                if isinstance(metadata, dict):
                    services.add(metadata.get('service', 'unknown'))
                    compartments.add(metadata.get('compartment', 'unknown'))
                    total_resources += metadata.get('resource_count', 0)

            return {
                "total_documents": count,
                "unique_services": len(services),
                "unique_compartments": len(compartments),
                "total_resources": total_resources,
                "services": list(services),
                "compartments": list(compartments)
            }
        except Exception as e:
            print(f"❌ Failed to get collection stats: {e}")
            return {"error": str(e)}

    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        try:
            # Get all document IDs
            all_docs = self.collection.get()
            if all_docs and 'ids' in all_docs and len(all_docs['ids']) > 0:
                self.collection.delete(ids=all_docs['ids'])
                print(
                    f"🗑️ Cleared {len(all_docs['ids'])} documents from enhanced collection")
            else:
                print("🗑️ Enhanced collection is already empty")
            return True
        except Exception as e:
            print(f"❌ Failed to clear enhanced collection: {e}")
            return False


# Global instance
_vector_store = None


def get_vector_store() -> EnhancedVectorStore:
    """Get global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = EnhancedVectorStore()
    return _vector_store

# Backward compatibility functions


def get_chroma_client():
    """Backward compatible function."""
    return get_vector_store().client


def get_or_create_collection(collection_name="oci_resources"):
    """Backward compatible function."""
    return get_vector_store().collection


def add_to_store(text: str, metadata: dict, embedding: list, doc_id: str = None):
    """Backward compatible function."""
    store = get_vector_store()
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    store.collection.add(
        documents=[text],
        metadatas=[metadata],
        embeddings=[embedding],
        ids=[doc_id]
    )
    return doc_id


def query_store(query: str, embedding: list, top_k: int = 3):
    """Backward compatible function."""
    store = get_vector_store()
    return store.search_resources(query, embedding, top_k)


def clear_store():
    """Backward compatible function."""
    store = get_vector_store()
    return store.clear_collection()
