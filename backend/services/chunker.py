"""Text chunking service for document processing.

Handles splitting documents into manageable chunks for embedding.
"""
import re
from typing import List, Tuple
from dataclasses import dataclass
import hashlib

from config.settings import CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS


@dataclass
class TextChunk:
    """Represents a text chunk with metadata."""
    text: str
    chunk_id: str
    source: str
    start_pos: int
    end_pos: int
    
    def __hash__(self):
        return hash(self.chunk_id)


class Chunker:
    """Splits text into overlapping chunks for embedding."""
    
    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE_CHARS,
        overlap: int = CHUNK_OVERLAP_CHARS
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(
        self,
        text: str,
        source: str = "unknown"
    ) -> List[TextChunk]:
        """Split text into overlapping chunks.
        
        Uses a sliding window approach with configurable overlap
        to maintain context across chunk boundaries.
        
        Args:
            text: Text to chunk
            source: Source document name
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        text = self._normalize_text(text)
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            
            # Try to end at a sentence boundary
            if end < len(text):
                end = self._find_boundary(text, start, end)
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunk_id = self._generate_chunk_id(source, chunk_index, chunk_text)
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_id=chunk_id,
                    source=source,
                    start_pos=start,
                    end_pos=end
                ))
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.overlap if end < len(text) else end
            
            # Prevent infinite loop
            if start >= len(text) - 1:
                break
        
        return chunks
    
    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace and clean text."""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def _find_boundary(self, text: str, start: int, end: int) -> int:
        """Find a natural sentence boundary near the end position.
        
        Looks for sentence-ending punctuation within a reasonable range.
        """
        # Look back up to 100 chars for a sentence boundary
        search_start = max(end - 100, start + self.chunk_size // 2)
        search_text = text[search_start:end]
        
        # Find last sentence boundary
        boundaries = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        last_boundary = -1
        
        for boundary in boundaries:
            pos = search_text.rfind(boundary)
            if pos > last_boundary:
                last_boundary = pos
        
        if last_boundary > 0:
            return search_start + last_boundary + 1
        
        # Fall back to word boundary
        word_boundary = search_text.rfind(' ')
        if word_boundary > 0:
            return search_start + word_boundary
        
        return end
    
    def _generate_chunk_id(self, source: str, index: int, text: str) -> str:
        """Generate a unique chunk ID."""
        content_hash = hashlib.md5(text[:100].encode()).hexdigest()[:8]
        return f"{source}_{index}_{content_hash}"
    
    def chunk_document(
        self,
        content: str,
        filename: str
    ) -> Tuple[List[TextChunk], dict]:
        """Chunk a document and return chunks with metadata.
        
        Args:
            content: Document content
            filename: Document filename
            
        Returns:
            Tuple of (chunks list, metadata dict)
        """
        chunks = self.chunk_text(content, source=filename)
        
        metadata = {
            'filename': filename,
            'chunk_count': len(chunks),
            'total_chars': len(content),
            'avg_chunk_size': len(content) // len(chunks) if chunks else 0
        }
        
        return chunks, metadata
