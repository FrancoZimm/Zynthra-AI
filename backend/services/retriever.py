"""Retrieval service for semantic search.

Handles query processing and context retrieval.
"""
from typing import List, Optional, Tuple
import logging

from config.settings import (
    TOP_K_RESULTS,
    LOCAL_CONFIDENCE_THRESHOLD,
    STRONG_LOCAL_CONFIDENCE_THRESHOLD
)
from models.schemas import EvidenceChunk
from .embeddings import Embedder
from .indexer import VectorIndex, IndexItem

logger = logging.getLogger(__name__)


class Retriever:
    """Performs semantic search with conversational context."""
    
    def __init__(
        self,
        embedder: Embedder,
        vector_index: VectorIndex
    ):
        self.embedder = embedder
        self.vector_index = vector_index
    
    async def retrieve(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        min_score: float = 0.0
    ) -> Tuple[List[EvidenceChunk], float]:
        """Retrieve relevant evidence for a query.
        
        Args:
            query: User query
            top_k: Maximum number of results
            min_score: Minimum relevance score
            
        Returns:
            Tuple of (evidence chunks, top score)
        """
        # Generate query embedding
        query_embedding = await self.embedder.embed_text(query)
        
        # Search index
        results = self.vector_index.search(
            query_embedding=query_embedding,
            top_k=top_k,
            min_score=min_score
        )
        
        # Convert to EvidenceChunk objects
        evidence = []
        top_score = 0.0
        
        for item, score in results:
            if score > top_score:
                top_score = score
            
            evidence.append(EvidenceChunk(
                text=item.text,
                source=item.source,
                score=score,
                chunk_id=item.chunk_id
            ))
        
        return evidence, top_score
    
    async def retrieve_with_context(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None,
        top_k: int = TOP_K_RESULTS
    ) -> Tuple[List[EvidenceChunk], float, str]:
        """Retrieve with conversation context consideration.
        
        Args:
            query: Current user query
            conversation_history: Previous conversation messages
            top_k: Maximum number of results
            
        Returns:
            Tuple of (evidence, top_score, enhanced_query)
        """
        # Build enhanced query from context
        enhanced_query = self._build_contextual_query(
            query, conversation_history
        )
        
        evidence, top_score = await self.retrieve(
            enhanced_query,
            top_k=top_k
        )
        
        return evidence, top_score, enhanced_query
    
    def _build_contextual_query(
        self,
        query: str,
        history: Optional[List[dict]] = None
    ) -> str:
        """Build query with conversation context.
        
        For follow-up questions, incorporate relevant context
        from previous messages.
        """
        if not history:
            return query
        
        # Check if this is a follow-up question
        follow_up_indicators = [
            'eso', 'esto', 'el', 'la', 'lo', 'ese', 'esa',
            'this', 'that', 'it', 'they', 'them',
            '¿y', '¿qué más', '¿cómo', '¿por qué',
            'and', 'what else', 'how', 'why'
        ]
        
        query_lower = query.lower()
        is_follow_up = any(ind in query_lower for ind in follow_up_indicators)
        
        if not is_follow_up:
            return query
        
        # Get last user message for context
        user_messages = [
            msg['content'] for msg in history 
            if msg.get('role') == 'user'
        ][-2:]  # Last 2 user messages
        
        if user_messages:
            context = " ".join(user_messages)
            return f"{context} {query}"
        
        return query
    
    def has_sufficient_evidence(
        self,
        top_score: float,
        threshold: Optional[float] = None
    ) -> bool:
        """Check if retrieved evidence is sufficient.
        
        Args:
            top_score: Highest relevance score from retrieval
            threshold: Optional custom threshold
            
        Returns:
            True if evidence is sufficient
        """
        threshold = threshold or LOCAL_CONFIDENCE_THRESHOLD
        return top_score >= threshold
    
    def has_strong_evidence(
        self,
        top_score: float,
        threshold: Optional[float] = None
    ) -> bool:
        """Check if evidence is strongly supported.
        
        Args:
            top_score: Highest relevance score
            threshold: Optional custom threshold
            
        Returns:
            True if evidence is strong
        """
        threshold = threshold or STRONG_LOCAL_CONFIDENCE_THRESHOLD
        return top_score >= threshold
    
    def format_evidence_context(self, evidence: List[EvidenceChunk]) -> str:
        """Format evidence chunks into context string for LLM.
        
        Args:
            evidence: List of evidence chunks
            
        Returns:
            Formatted context string
        """
        if not evidence:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(evidence, 1):
            context_parts.append(
                f"[Fuente {i}: {chunk.source}]\n{chunk.text}\n"
            )
        
        return "\n".join(context_parts)
