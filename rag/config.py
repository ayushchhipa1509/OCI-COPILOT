# rag/config.py - RAG Configuration

import os
from typing import Dict, Any, List


class RAGConfig:
    """Configuration for RAG system."""

    # Embedding Configuration
    EMBEDDING_MODEL = "text-embedding-3-small"  # Newer, more efficient model
    EMBEDDING_DIMENSIONS = 1536
    EMBEDDING_CACHE_SIZE = 1000
    EMBEDDING_CACHE_FILE = "rag/embedding_cache.json"

    # Vector Store Configuration
    VECTOR_STORE_PATH = "rag/chroma_db"
    COLLECTION_NAME = "oci_resources_enhanced"
    SIMILARITY_METRIC = "cosine"

    # Retrieval Configuration
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 20
    MIN_RELEVANCE_THRESHOLD = 0.3

    # Query Processing
    QUERY_EXPANSION_ENABLED = True
    QUERY_FILTERING_ENABLED = True
    QUERY_RANKING_ENABLED = True

    # Tenancy Scanner Configuration
    RESOURCE_PREVIEW_LIMIT = 15
    MAX_COMPARTMENTS_PER_SCAN = 50
    SCAN_TIMEOUT_SECONDS = 300

    # Performance Configuration
    BATCH_SIZE_FOR_EMBEDDINGS = 10
    CACHE_EMBEDDINGS = True
    PARALLEL_PROCESSING = True

    # Service Priorities
    SERVICE_PRIORITIES = {
        "compute": "high",
        "blockstorage": "high",
        "virtualnetwork": "high",
        "database": "high",
        "identity": "high",
        "objectstorage": "medium",
        "loadbalancer": "medium",
        "cloudguard": "medium",
        "monitoring": "low",
        "optimizer": "low"
    }

    # Query Expansion Patterns
    QUERY_EXPANSIONS = {
        "instances": ["compute", "vm", "virtual machine", "server"],
        "volumes": ["storage", "disk", "block storage"],
        "buckets": ["object storage", "s3", "blob storage"],
        "users": ["identity", "iam", "accounts"],
        "networks": ["vcn", "subnet", "security list", "load balancer"],
        "databases": ["db", "database", "autonomous database", "db system"],
        "running": ["active", "up", "started"],
        "stopped": ["inactive", "down", "shutdown"],
        "list": ["show", "get", "find", "display", "view"],
        "count": ["how many", "number of", "total"]
    }

    # Service-specific Resource Fields
    RESOURCE_FIELDS = {
        "compute": ["display_name", "lifecycle_state", "shape", "availability_domain"],
        "blockstorage": ["display_name", "lifecycle_state", "size_in_gbs", "availability_domain"],
        "virtualnetwork": ["display_name", "lifecycle_state", "cidr_block", "dns_label"],
        "identity": ["name", "lifecycle_state", "email", "is_mfa_activated"],
        "database": ["display_name", "lifecycle_state", "shape", "availability_domain"],
        "objectstorage": ["name", "namespace", "time_created"],
        "loadbalancer": ["display_name", "lifecycle_state", "shape_name", "subnet_ids"],
        "cloudguard": ["display_name", "lifecycle_state", "detector_type"],
        "monitoring": ["display_name", "lifecycle_state", "metric_compartment_id"],
        "optimizer": ["name", "lifecycle_state", "importance", "resource_type"]
    }

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return {
            "embedding": {
                "model": cls.EMBEDDING_MODEL,
                "dimensions": cls.EMBEDDING_DIMENSIONS,
                "cache_size": cls.EMBEDDING_CACHE_SIZE,
                "cache_file": cls.EMBEDDING_CACHE_FILE
            },
            "vector_store": {
                "path": cls.VECTOR_STORE_PATH,
                "collection_name": cls.COLLECTION_NAME,
                "similarity_metric": cls.SIMILARITY_METRIC
            },
            "retrieval": {
                "default_top_k": cls.DEFAULT_TOP_K,
                "max_top_k": cls.MAX_TOP_K,
                "min_relevance_threshold": cls.MIN_RELEVANCE_THRESHOLD,
                "query_expansion_enabled": cls.QUERY_EXPANSION_ENABLED,
                "query_filtering_enabled": cls.QUERY_FILTERING_ENABLED,
                "query_ranking_enabled": cls.QUERY_RANKING_ENABLED
            },
            "scanner": {
                "resource_preview_limit": cls.RESOURCE_PREVIEW_LIMIT,
                "max_compartments_per_scan": cls.MAX_COMPARTMENTS_PER_SCAN,
                "scan_timeout_seconds": cls.SCAN_TIMEOUT_SECONDS
            },
            "performance": {
                "batch_size_for_embeddings": cls.BATCH_SIZE_FOR_EMBEDDINGS,
                "cache_embeddings": cls.CACHE_EMBEDDINGS,
                "parallel_processing": cls.PARALLEL_PROCESSING
            },
            "service_priorities": cls.SERVICE_PRIORITIES,
            "query_expansions": cls.QUERY_EXPANSIONS,
            "resource_fields": cls.RESOURCE_FIELDS
        }

    @classmethod
    def update_config(cls, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        for key, value in updates.items():
            if hasattr(cls, key.upper()):
                setattr(cls, key.upper(), value)

    @classmethod
    def get_service_priority(cls, service: str) -> str:
        """Get priority for a service."""
        return cls.SERVICE_PRIORITIES.get(service, "medium")

    @classmethod
    def get_resource_fields(cls, service: str) -> List[str]:
        """Get resource fields for a service."""
        return cls.RESOURCE_FIELDS.get(service, ["display_name", "lifecycle_state"])

    @classmethod
    def get_query_expansions(cls, term: str) -> List[str]:
        """Get query expansions for a term."""
        return cls.QUERY_EXPANSIONS.get(term.lower(), [term])

# Environment-specific overrides


def load_env_config():
    """Load configuration from environment variables."""
    config_updates = {}

    # Embedding configuration
    if os.getenv('RAG_EMBEDDING_MODEL'):
        config_updates['embedding_model'] = os.getenv('RAG_EMBEDDING_MODEL')

    if os.getenv('RAG_EMBEDDING_CACHE_SIZE'):
        config_updates['embedding_cache_size'] = int(
            os.getenv('RAG_EMBEDDING_CACHE_SIZE'))

    # Vector store configuration
    if os.getenv('RAG_VECTOR_STORE_PATH'):
        config_updates['vector_store_path'] = os.getenv(
            'RAG_VECTOR_STORE_PATH')

    # Retrieval configuration
    if os.getenv('RAG_DEFAULT_TOP_K'):
        config_updates['default_top_k'] = int(os.getenv('RAG_DEFAULT_TOP_K'))

    if os.getenv('RAG_MIN_RELEVANCE_THRESHOLD'):
        config_updates['min_relevance_threshold'] = float(
            os.getenv('RAG_MIN_RELEVANCE_THRESHOLD'))

    # Scanner configuration
    if os.getenv('RAG_RESOURCE_PREVIEW_LIMIT'):
        config_updates['resource_preview_limit'] = int(
            os.getenv('RAG_RESOURCE_PREVIEW_LIMIT'))

    # Performance configuration
    if os.getenv('RAG_BATCH_SIZE_FOR_EMBEDDINGS'):
        config_updates['batch_size_for_embeddings'] = int(
            os.getenv('RAG_BATCH_SIZE_FOR_EMBEDDINGS'))

    if os.getenv('RAG_CACHE_EMBEDDINGS'):
        config_updates['cache_embeddings'] = os.getenv(
            'RAG_CACHE_EMBEDDINGS').lower() == 'true'

    # Apply updates
    if config_updates:
        RAGConfig.update_config(config_updates)
        print(
            f"🔧 Loaded {len(config_updates)} environment configuration overrides")


# Load environment configuration on import
load_env_config()
