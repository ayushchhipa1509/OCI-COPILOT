# rag/init_rag.py - RAG System Initialization

import os
import sys
from typing import Dict, Any

# Add the parent directory to the path so we can import rag modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def initialize_rag_system() -> Dict[str, Any]:
    """
    Initialize the RAG system by creating necessary directories and collections.
    Returns initialization status and any errors encountered.
    """
    print("🚀 Initializing Enhanced RAG System...")

    initialization_results = {
        "success": True,
        "steps_completed": [],
        "errors": [],
        "warnings": []
    }

    try:
        # Step 1: Create necessary directories
        print("📁 Creating RAG directories...")
        rag_dir = os.path.join(os.path.dirname(__file__))
        chroma_dir = os.path.join(rag_dir, "chroma_db")
        cache_dir = os.path.join(rag_dir)

        os.makedirs(chroma_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)

        initialization_results["steps_completed"].append(
            "Created RAG directories")
        print("✅ RAG directories created")

        # Step 2: Initialize vector store
        print("📚 Initializing vector store...")
        try:
            from rag.vectorstore import get_vector_store
            vector_store = get_vector_store()
            initialization_results["steps_completed"].append(
                "Vector store initialized")
            print("✅ Vector store initialized")
        except Exception as e:
            initialization_results["errors"].append(
                f"Vector store initialization failed: {e}")
            initialization_results["success"] = False
            print(f"❌ Vector store initialization failed: {e}")

        # Step 3: Initialize embedding manager
        print("🔤 Initializing embedding manager...")
        try:
            from rag.embeddings import get_embedding_manager
            embedding_manager = get_embedding_manager()
            initialization_results["steps_completed"].append(
                "Embedding manager initialized")
            print("✅ Embedding manager initialized")
        except Exception as e:
            initialization_results["errors"].append(
                f"Embedding manager initialization failed: {e}")
            initialization_results["success"] = False
            print(f"❌ Embedding manager initialization failed: {e}")

        # Step 4: Test basic functionality
        print("🧪 Testing basic functionality...")
        try:
            # Test embedding generation
            test_embedding = embedding_manager.get_embedding("test query")
            if len(test_embedding) == 1536:
                initialization_results["steps_completed"].append(
                    "Embedding generation test passed")
                print("✅ Embedding generation test passed")
            else:
                initialization_results["warnings"].append(
                    "Embedding generation test failed - wrong dimensions")
                print("⚠️ Embedding generation test failed - wrong dimensions")

            # Test vector store stats
            stats = vector_store.get_collection_stats()
            if "error" not in stats:
                initialization_results["steps_completed"].append(
                    "Vector store stats test passed")
                print("✅ Vector store stats test passed")
            else:
                initialization_results["warnings"].append(
                    "Vector store stats test failed - collection empty")
                print(
                    "⚠️ Vector store stats test failed - collection empty (this is normal for new setup)")

        except Exception as e:
            initialization_results["errors"].append(
                f"Basic functionality test failed: {e}")
            initialization_results["success"] = False
            print(f"❌ Basic functionality test failed: {e}")

        # Step 5: Check environment variables
        print("🔧 Checking environment configuration...")
        # Preferred but not required due to fallback
        preferred_env_vars = ["OPENAI_API_KEY"]
        optional_env_vars = ["GOOGLE_API_KEY", "GROQ_API_KEY"]

        missing_preferred = []
        missing_optional = []

        for var in preferred_env_vars:
            if not os.getenv(var):
                missing_preferred.append(var)

        for var in optional_env_vars:
            if not os.getenv(var):
                missing_optional.append(var)

        if missing_preferred:
            initialization_results["warnings"].append(
                f"Missing preferred environment variables: {', '.join(missing_preferred)} (using fallback)")
            print(
                f"⚠️ Missing preferred environment variables: {', '.join(missing_preferred)} (using sentence-transformers fallback)")
        else:
            initialization_results["steps_completed"].append(
                "Environment variables check passed")
            print("✅ Preferred environment variables found")

        if missing_optional:
            initialization_results["warnings"].append(
                f"Missing optional environment variables: {', '.join(missing_optional)}")
            print(
                f"⚠️ Missing optional environment variables: {', '.join(missing_optional)}")

        # Note: We don't fail initialization due to missing API keys since we have fallbacks

        # Final status
        if initialization_results["success"]:
            print("🎉 RAG System initialization completed successfully!")
            print(
                f"📊 Completed steps: {len(initialization_results['steps_completed'])}")
            if initialization_results["warnings"]:
                print(
                    f"⚠️ Warnings: {len(initialization_results['warnings'])}")
        else:
            print("❌ RAG System initialization failed!")
            print(f"💥 Errors: {len(initialization_results['errors'])}")

    except Exception as e:
        initialization_results["success"] = False
        initialization_results["errors"].append(
            f"Unexpected error during initialization: {e}")
        print(f"💥 Unexpected error during initialization: {e}")

    return initialization_results


def check_rag_health() -> Dict[str, Any]:
    """
    Check the health of the RAG system.
    Returns health status and diagnostics.
    """
    print("🏥 Checking RAG System Health...")

    health_status = {
        "healthy": True,
        "components": {},
        "issues": [],
        "recommendations": []
    }

    try:
        # Check vector store
        try:
            from rag.vectorstore import get_vector_store
            vector_store = get_vector_store()
            stats = vector_store.get_collection_stats()

            if "error" in stats:
                health_status["components"]["vector_store"] = "error"
                health_status["issues"].append(
                    f"Vector store error: {stats['error']}")
                health_status["healthy"] = False
            else:
                health_status["components"]["vector_store"] = "healthy"
                health_status["components"]["vector_store_stats"] = stats

        except Exception as e:
            health_status["components"]["vector_store"] = "error"
            health_status["issues"].append(f"Vector store check failed: {e}")
            health_status["healthy"] = False

        # Check embedding manager
        try:
            from rag.embeddings import get_embedding_manager
            embedding_manager = get_embedding_manager()

            # Test embedding generation
            test_embedding = embedding_manager.get_embedding("health check")
            if len(test_embedding) == 1536:
                health_status["components"]["embedding_manager"] = "healthy"
            else:
                health_status["components"]["embedding_manager"] = "warning"
                health_status["issues"].append(
                    "Embedding generation returned wrong dimensions")

        except Exception as e:
            health_status["components"]["embedding_manager"] = "error"
            health_status["issues"].append(
                f"Embedding manager check failed: {e}")
            health_status["healthy"] = False

        # Check retriever
        try:
            from rag.retriever import get_enhanced_retriever
            retriever = get_enhanced_retriever()
            health_status["components"]["retriever"] = "healthy"
        except Exception as e:
            health_status["components"]["retriever"] = "error"
            health_status["issues"].append(f"Retriever check failed: {e}")
            health_status["healthy"] = False

        # Generate recommendations
        if not health_status["healthy"]:
            health_status["recommendations"].append(
                "Run 'Scan Master Tenancy' to populate the vector store")
            health_status["recommendations"].append(
                "Check environment variables for API keys")
            health_status["recommendations"].append(
                "Verify OCI credentials are properly configured")

        if health_status["components"].get("vector_store") == "healthy":
            stats = health_status["components"].get("vector_store_stats", {})
            if stats.get("total_documents", 0) == 0:
                health_status["recommendations"].append(
                    "Vector store is empty - run a master scan to populate it")

        print(
            f"🏥 Health check completed: {'✅ Healthy' if health_status['healthy'] else '❌ Issues found'}")

    except Exception as e:
        health_status["healthy"] = False
        health_status["issues"].append(f"Health check failed: {e}")
        print(f"💥 Health check failed: {e}")

    return health_status


if __name__ == "__main__":
    # Run initialization when script is executed directly
    print("🚀 RAG System Initialization Script")
    print("=" * 50)

    # Initialize the system
    init_results = initialize_rag_system()

    print("\n" + "=" * 50)
    print("🏥 Running Health Check...")

    # Check system health
    health_results = check_rag_health()

    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(
        f"   Initialization: {'✅ Success' if init_results['success'] else '❌ Failed'}")
    print(
        f"   System Health: {'✅ Healthy' if health_results['healthy'] else '❌ Issues'}")
    print(f"   Steps Completed: {len(init_results['steps_completed'])}")
    print(
        f"   Issues Found: {len(init_results['errors']) + len(health_results['issues'])}")

    if init_results["warnings"] or health_results["recommendations"]:
        print("\n💡 Recommendations:")
        for warning in init_results["warnings"]:
            print(f"   ⚠️ {warning}")
        for rec in health_results["recommendations"]:
            print(f"   💡 {rec}")

    if not init_results["success"] or not health_results["healthy"]:
        print("\n❌ RAG System needs attention before use!")
        sys.exit(1)
    else:
        print("\n🎉 RAG System is ready for use!")
        sys.exit(0)
