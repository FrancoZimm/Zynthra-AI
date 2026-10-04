"""Index service for managing vector index.

Handles indexing, storage, and retrieval of document embeddings.
"""
import json
import gzip
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from datetime import datetime

from config.settings import INDEX_DIR
from .chunker import TextChunk

logger = logging.getLogger(__name__)


@dataclass
class IndexItem:
    """Item stored in the vector index."""
    chunk_id: str
    source: str
    text: str
    embedding: List[float]
    indexed_at: str = ""
    
    def __post_init__(self):
        if not self.indexed_at:
            self.indexed_at = datetime.utcnow().isoformat()


class VectorIndex:
    """Persistent vector index with fast cosine similarity search."""
    
    def __init__(self, index_dir: Path = INDEX_DIR):
        self.index_dir = index_dir
        self.index_path = index_dir / "rag_index.json.gz"
        self._index: List[IndexItem] = []
        self._embeddings_matrix: Optional[np.ndarray] = None
        self._load_index()
    
    def _load_index(self):
        """Load index from disk."""
        if not self.index_path.exists():
            logger.info("No existing index found, starting fresh")
            return
        
        try:
            with gzip.open(self.index_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            self._index = [
                IndexItem(**item) for item in data.get('items', [])
            ]
            self._rebuild_matrix()
            logger.info(f"Loaded index with {len(self._index)} items")
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            self._index = []
    
    def _save_index(self):
        """Save index to disk."""
        try:
            self.index_dir.mkdir(exist_ok=True)
            data = {
                'items': [asdict(item) for item in self._index],
                'updated_at': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
            with gzip.open(self.index_path, 'wt', encoding='utf-8') as f:
                json.dump(data, f)
            
            logger.info(f"Saved index with {len(self._index)} items")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    def _rebuild_matrix(self):
        """Rebuild numpy matrix for fast similarity search."""
        if not self._index:
            self._embeddings_matrix = None
            return
        
        embeddings = [item.embedding for item in self._index]
        self._embeddings_matrix = np.array(embeddings, dtype=np.float32)
    
    def add_items(
        self,
        chunks: List[TextChunk],
        embeddings: List[List[float]]
    ) -> int:
        """Add items to the index.
        
        Args:
            chunks: Text chunks to index
            embeddings: Corresponding embedding vectors
            
        Returns:
            Number of items added
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")
        
        # Deduplicate by chunk_id
        existing_ids = {item.chunk_id for item in self._index}
        added = 0
        
        for chunk, embedding in zip(chunks, embeddings):
            if chunk.chunk_id not in existing_ids:
                self._index.append(IndexItem(
                    chunk_id=chunk.chunk_id,
                    source=chunk.source,
                    text=chunk.text,
                    embedding=embedding
                ))
                existing_ids.add(chunk.chunk_id)
                added += 1
        
        if added > 0:
            self._rebuild_matrix()
            self._save_index()
        
        return added
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Tuple[IndexItem, float]]:
        """Search index for similar items.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            min_score: Minimum similarity score
            
        Returns:
            List of (IndexItem, score) tuples sorted by score descending
        """
        if not self._index or self._embeddings_matrix is None:
            return []
        
        # Convert query to numpy array
        query = np.array(query_embedding, dtype=np.float32)
        
        # Calculate cosine similarity (dot product for normalized vectors)
        scores = np.dot(self._embeddings_matrix, query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score >= min_score:
                results.append((self._index[idx], score))
        
        return results
    
    def remove_by_source(self, source: str) -> int:
        """Remove all items from a specific source.
        
        Args:
            source: Source document name
            
        Returns:
            Number of items removed
        """
        original_count = len(self._index)
        self._index = [item for item in self._index if item.source != source]
        removed = original_count - len(self._index)
        
        if removed > 0:
            self._rebuild_matrix()
            self._save_index()
        
        return removed
    
    def clear(self):
        """Clear all items from index."""
        self._index = []
        self._embeddings_matrix = None
        self._save_index()
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        sources = set(item.source for item in self._index)
        return {
            'total_items': len(self._index),
            'unique_sources': len(sources),
            'sources': list(sources),
            'index_path': str(self.index_path),
            'index_exists': self.index_path.exists()
        }
    
    def get_sources(self) -> List[str]:
        """Get list of indexed document sources."""
        return list(set(item.source for item in self._index))
    
    @property
    def count(self) -> int:
        """Return number of items in index."""
        return len(self._index)
