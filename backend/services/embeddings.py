"""Embedding service for generating vector representations.

Handles communication with Ollama for embedding generation.
"""
import numpy as np
from typing import List, Optional
import httpx
import logging
import asyncio
from functools import lru_cache

from config.settings import (
    OLLAMA_HOST,
    DEFAULT_EMBEDDING_MODEL,
    OLLAMA_TIMEOUT
)

logger = logging.getLogger(__name__)


class Embedder:
    """Generates vector embeddings via Ollama."""
    
    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        host: str = OLLAMA_HOST
    ):
        self.model = model
        self.host = host
        self._cache = {}
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=OLLAMA_TIMEOUT)
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return f"{self.model}:{hash(text)}"
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        # Check cache first
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.host}/api/embed",
                json={
                    "model": self.model,
                    "input": text
                }
            )
            response.raise_for_status()
            result = response.json()
            
            embedding = result["embeddings"][0]
            
            # L2 normalize embedding
            embedding = self._l2_normalize(embedding)
            
            # Cache result
            self._cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Check which texts are cached
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                embeddings.append((i, self._cache[cache_key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Fetch uncached embeddings
        if uncached_texts:
            try:
                client = await self._get_client()
                response = await client.post(
                    f"{self.host}/api/embed",
                    json={
                        "model": self.model,
                        "input": uncached_texts
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                new_embeddings = result["embeddings"]
                
                for j, (idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                    normalized = self._l2_normalize(new_embeddings[j])
                    self._cache[self._cache_key(text)] = normalized
                    embeddings.append((idx, normalized))
                    
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                raise
        
        # Sort by original index and return
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]
    
    def _l2_normalize(self, vector: List[float]) -> List[float]:
        """L2 normalize a vector."""
        arr = np.array(vector)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()
    
    async def check_health(self) -> bool:
        """Check if embedding service is available."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear embedding cache."""
        self._cache.clear()
