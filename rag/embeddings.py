# rag/embeddings.py - Enhanced Version

import openai
import os
import hashlib
import json
from typing import List, Dict, Any, Optional
from functools import lru_cache
import time

# Load environment variables early
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class EmbeddingManager:
    """Enhanced embedding manager with caching, fallbacks, and chunking."""

    def __init__(self):
        self.cache = {}
        self.cache_file = "rag/embedding_cache.json"
        self.load_cache()

    def load_cache(self):
        """Load embedding cache from disk."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"📚 Loaded {len(self.cache)} cached embeddings")
        except Exception as e:
            print(f"⚠️ Failed to load embedding cache: {e}")
            self.cache = {}

    def save_cache(self):
        """Save embedding cache to disk."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"⚠️ Failed to save embedding cache: {e}")

    def get_text_hash(self, text: str) -> str:
        """Generate hash for text to use as cache key."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def chunk_text(self, text: str, max_chunk_size: int = 8000) -> List[str]:
        """Split large text into chunks for embedding."""
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        sentences = text.split('. ')
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def get_embedding_openai(self, text: str) -> Optional[List[float]]:
        """Get embedding from OpenAI."""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            model = "text-embedding-3-small"  # Newer, more efficient model

            response = client.embeddings.create(
                input=text,
                model=model,
                dimensions=1536  # Match ada-002 dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ OpenAI embedding failed: {e}")
            return None

    def get_embedding_sentence_transformers(self, text: str) -> Optional[List[float]]:
        """Fallback to sentence-transformers for local embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text)
            # Convert to list and normalize dimensions
            return embedding.tolist()[:1536] + [0.0] * max(0, 1536 - len(embedding))
        except Exception as e:
            print(f"❌ Sentence-transformers embedding failed: {e}")
            return None

    def get_embedding(self, text: str, provider: str = "openai", use_cache: bool = True) -> List[float]:
        """
        Get embedding with caching and fallback providers.

        Args:
            text: Text to embed
            provider: Preferred provider ("openai", "sentence_transformers")
            use_cache: Whether to use cached embeddings

        Returns:
            Embedding vector (1536 dimensions)
        """
        if not text or not text.strip():
            return [0.0] * 1536

        # Clean and normalize text
        text = text.strip()

        # Check cache first
        if use_cache:
            text_hash = self.get_text_hash(text)
            if text_hash in self.cache:
                print(
                    f"📚 Using cached embedding for text hash: {text_hash[:8]}...")
                return self.cache[text_hash]

        # Try providers in order
        providers = [provider, "openai", "sentence_transformers"]
        embedding = None

        for current_provider in providers:
            if current_provider == "openai":
                embedding = self.get_embedding_openai(text)
            elif current_provider == "sentence_transformers":
                embedding = self.get_embedding_sentence_transformers(text)

            if embedding:
                print(f"🔤 Generated embedding using {current_provider}")
                break

        # Cache the result
        if embedding and use_cache:
            text_hash = self.get_text_hash(text)
            self.cache[text_hash] = embedding
            self.save_cache()

        # Fallback to dummy embedding
        if not embedding:
            print(f"⚠️ All embedding providers failed, using dummy embedding")
            embedding = [0.0] * 1536

        return embedding

    def get_embeddings_batch(self, texts: List[str], provider: str = "openai") -> List[List[float]]:
        """Get embeddings for multiple texts efficiently."""
        embeddings = []

        for text in texts:
            embedding = self.get_embedding(text, provider)
            embeddings.append(embedding)

        return embeddings

    def clear_cache(self):
        """Clear embedding cache."""
        self.cache = {}
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            print("🗑️ Embedding cache cleared")
        except Exception as e:
            print(f"⚠️ Failed to clear cache file: {e}")


# Global instance
_embedding_manager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get global embedding manager instance."""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager


def get_embedding(text: str, provider: str = "openai") -> List[float]:
    """Backward compatible function."""
    manager = get_embedding_manager()
    return manager.get_embedding(text, provider)


def get_embeddings_batch(texts: List[str], provider: str = "openai") -> List[List[float]]:
    """Get embeddings for multiple texts."""
    manager = get_embedding_manager()
    return manager.get_embeddings_batch(texts, provider)


def clear_embedding_cache():
    """Clear embedding cache."""
    manager = get_embedding_manager()
    manager.clear_cache()
