"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid


class IntentType(str, Enum):
    """User intent classification types."""
    LEGITIMATE_STUDY = "legitimate_study"
    COPY_ATTEMPT = "copy_attempt"
    SMALLTALK = "smalltalk"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class ResponseMode(str, Enum):
    """Response mode based on intent classification."""
    FULL_RESPONSE = "full_response"
    GUIDED_MODE = "guided_mode"
    CONVERSATIONAL = "conversational"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ChatMessage(BaseModel):
    """Single chat message."""
    model_config = ConfigDict(extra="ignore")
    
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.utcnow())


class ChatRequest(BaseModel):
    """Chat request from frontend."""
    model_config = ConfigDict(extra="ignore")
    
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    include_evidence: bool = Field(default=True, description="Include source evidence in response")
    confidence_threshold: Optional[float] = Field(default=None, description="Override default confidence threshold")


class EvidenceChunk(BaseModel):
    """Evidence chunk from RAG retrieval."""
    model_config = ConfigDict(extra="ignore")
    
    text: str = Field(..., description="Chunk text content")
    source: str = Field(..., description="Source document name")
    score: float = Field(..., description="Relevance score 0-1")
    chunk_id: str = Field(..., description="Unique chunk identifier")


class IntentClassification(BaseModel):
    """Intent classification result."""
    model_config = ConfigDict(extra="ignore")
    
    intent_type: IntentType = Field(..., description="Classified intent type")
    confidence: float = Field(..., description="Classification confidence 0-1")
    triggered_patterns: List[str] = Field(default_factory=list, description="Patterns that triggered classification")
    recommended_mode: ResponseMode = Field(..., description="Recommended response mode")


class ChatResponse(BaseModel):
    """Chat response to frontend."""
    model_config = ConfigDict(extra="ignore")
    
    response: str = Field(..., description="AI response text")
    conversation_id: str = Field(..., description="Conversation ID")
    response_mode: ResponseMode = Field(..., description="Response mode used")
    evidence: List[EvidenceChunk] = Field(default_factory=list, description="Supporting evidence")
    confidence_score: float = Field(..., description="Overall confidence in response")
    intent_classification: Optional[IntentClassification] = Field(default=None)
    is_guided_mode: bool = Field(default=False, description="Whether guided mode was triggered")
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())


class Document(BaseModel):
    """Indexed document metadata."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content_preview: str = Field(default="", description="First 200 chars of content")
    chunk_count: int = Field(default=0)
    indexed_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    file_size: int = Field(default=0, description="File size in bytes")
    file_type: str = Field(default="txt")


class DocumentUpload(BaseModel):
    """Document upload request."""
    model_config = ConfigDict(extra="ignore")
    
    filename: str
    content: str
    file_type: str = Field(default="txt")


class ConversationHistory(BaseModel):
    """Conversation history for a session."""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    document_context: List[str] = Field(default_factory=list, description="IDs of related documents")


class SystemStatus(BaseModel):
    """System health status."""
    model_config = ConfigDict(extra="ignore")
    
    status: str = Field(default="healthy")
    ollama_available: bool = Field(default=False)
    ollama_error: str = Field(default="", description="Error message if Ollama unavailable")
    ollama_host: str = Field(default="", description="Ollama host URL being used")
    documents_indexed: int = Field(default=0)
    model_loaded: str = Field(default="")
    embedding_model: str = Field(default="")
    memory_usage_mb: float = Field(default=0.0)


class RAGResponse(BaseModel):
    """Internal RAG pipeline response."""
    model_config = ConfigDict(extra="ignore")
    
    answer: str
    evidence: List[EvidenceChunk]
    top_score: float
    has_sufficient_evidence: bool
    query_used: str
