"""Data models for the Tutor IA Verificable application."""
from .schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Document,
    DocumentUpload,
    EvidenceChunk,
    RAGResponse,
    ConversationHistory,
    SystemStatus,
    IntentClassification
)

__all__ = [
    'ChatMessage',
    'ChatRequest', 
    'ChatResponse',
    'Document',
    'DocumentUpload',
    'EvidenceChunk',
    'RAGResponse',
    'ConversationHistory',
    'SystemStatus',
    'IntentClassification'
]
