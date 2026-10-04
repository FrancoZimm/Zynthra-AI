"""Zynthra-AI Core Orchestrator.

Main coordinator that routes user messages through:
intent classification → retrieval → LLM generation.
"""
import logging
from typing import Optional, List, AsyncGenerator
import uuid

from config.settings import (
    LOCAL_CONFIDENCE_THRESHOLD,
    ENABLE_ANTI_COPY
)
from config.prompts import INSUFFICIENT_EVIDENCE_MESSAGE
from models.schemas import (
    ChatRequest,
    ChatResponse,
    EvidenceChunk,
    ResponseMode,
    IntentType
)
from .embeddings import Embedder
from .indexer import VectorIndex
from .retriever import Retriever
from .intent import IntentClassifier
from .llm import LLM
from .chunker import Chunker

logger = logging.getLogger(__name__)


class ZynthraCore:
    """Main orchestrator for the Zynthra-AI pipeline."""
    
    def __init__(self):
        self.embedder = Embedder()
        self.vector_index = VectorIndex()
        self.retriever = Retriever(self.embedder, self.vector_index)
        self.intent_classifier = IntentClassifier()
        self.llm = LLM()
        self.chunker = Chunker()
        
        # Conversation memory (in-memory; swap for DB to persist)
        self._conversations: dict = {}
    
    async def close(self):
        """Cleanup resources."""
        await self.embedder.close()
        await self.llm.close()
    
    def _get_conversation_history(
        self,
        conversation_id: Optional[str]
    ) -> List[dict]:
        """Get conversation history."""
        if not conversation_id:
            return []
        return self._conversations.get(conversation_id, [])
    
    def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ):
        """Save message to conversation history."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        
        self._conversations[conversation_id].append({
            "role": role,
            "content": content
        })
        
        # Keep only last 20 messages
        if len(self._conversations[conversation_id]) > 20:
            self._conversations[conversation_id] = \
                self._conversations[conversation_id][-20:]
    
    async def process_message(
        self,
        request: ChatRequest
    ) -> ChatResponse:
        """Process a chat message through the RAG pipeline.
        
        Args:
            request: Chat request with message and options
            
        Returns:
            ChatResponse with generated answer and evidence
        """
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        history = self._get_conversation_history(conversation_id)
        
        # Classify user intent
        intent = self.intent_classifier.classify(
            request.message,
            history
        )
        
        logger.info(
            f"Intent: {intent.intent_type}, confidence: {intent.confidence}"
        )
        
        # Check if Ollama is available
        ollama_available, _ = await self.llm.check_health()
        
        if not ollama_available:
            # Demo mode: Return helpful message when Ollama is not available
            demo_response = self._get_demo_response(request.message, intent)
            
            # In demo, still flag copy attempts as guided mode for UI demonstration
            is_guided = intent.intent_type == IntentType.COPY_ATTEMPT and intent.confidence > 0.6
            
            self._save_message(conversation_id, "user", request.message)
            self._save_message(conversation_id, "assistant", demo_response)
            
            return ChatResponse(
                response=demo_response,
                conversation_id=conversation_id,
                response_mode=ResponseMode.GUIDED_MODE if is_guided else ResponseMode.FULL_RESPONSE,
                evidence=[],
                confidence_score=0.0,
                intent_classification=intent,
                is_guided_mode=is_guided
            )
        
        # Handle smalltalk without RAG
        if intent.intent_type == IntentType.SMALLTALK:
            response_text = await self.llm.generate(
                request.message,
                context="",
                mode=ResponseMode.CONVERSATIONAL,
                history=history
            )
            
            self._save_message(conversation_id, "user", request.message)
            self._save_message(conversation_id, "assistant", response_text)
            
            return ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                response_mode=ResponseMode.CONVERSATIONAL,
                evidence=[],
                confidence_score=1.0,
                intent_classification=intent,
                is_guided_mode=False
            )
        
        # Retrieve relevant evidence
        threshold = request.confidence_threshold or LOCAL_CONFIDENCE_THRESHOLD
        evidence, top_score, enhanced_query = await self.retriever.retrieve_with_context(
            request.message,
            history
        )
        
        # Check if we have sufficient evidence
        has_evidence = self.retriever.has_sufficient_evidence(
            top_score, threshold
        )
        
        # Determine response mode
        if not has_evidence:
            response_mode = ResponseMode.INSUFFICIENT_EVIDENCE
        elif ENABLE_ANTI_COPY and self.intent_classifier.should_activate_guided_mode(
            intent, top_score
        ):
            response_mode = ResponseMode.GUIDED_MODE
        else:
            response_mode = intent.recommended_mode
        
        # Generate response based on mode
        if response_mode == ResponseMode.INSUFFICIENT_EVIDENCE:
            doc_count = self.vector_index.count
            response_text = INSUFFICIENT_EVIDENCE_MESSAGE['es'].format(
                document_count=doc_count
            )
        else:
            # Format evidence context
            context = self.retriever.format_evidence_context(
                evidence[:5]  # Top 5 chunks
            )
            
            response_text = await self.llm.generate(
                request.message,
                context=context,
                mode=response_mode,
                history=history
            )
        
        # Save to conversation history
        self._save_message(conversation_id, "user", request.message)
        self._save_message(conversation_id, "assistant", response_text)
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            response_mode=response_mode,
            evidence=evidence if request.include_evidence else [],
            confidence_score=top_score,
            intent_classification=intent,
            is_guided_mode=response_mode == ResponseMode.GUIDED_MODE
        )
    
    def _get_demo_response(self, message: str, intent) -> str:
        """Get a demo response when Ollama is not available."""
        if intent.intent_type == IntentType.SMALLTALK:
            return "¡Hola! Soy Zynthra-AI. Actualmente estoy en modo demo porque Ollama no está conectado. Para funcionar completamente, necesitas tener Ollama ejecutándose localmente."
        
        if intent.intent_type == IntentType.COPY_ATTEMPT:
            return """**⚠️ Modo Demo - Ollama no conectado**

Detecté una solicitud que podría activar el **Modo Guiado Anti-copia**.

En producción, si detectamos intención de copiar sin comprensión, el sistema:
1. Hace preguntas diagnósticas
2. Pide demostrar comprensión previa
3. Ofrece pistas graduales
4. Divide problemas en pasos

**Para probar la funcionalidad completa:**
1. Instala Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Descarga un modelo: `ollama pull llama3.2:1b`
3. Descarga embeddings: `ollama pull nomic-embed-text`"""
        
        return f"""**🔧 Modo Demo - Sistema RAG**

Tu pregunta: *"{message[:100]}..."*

**En producción, este sistema:**
1. 📚 Busca en documentos indexados
2. 🎯 Recupera evidencia relevante
3. ✅ Genera respuestas verificables
4. 🛡️ Detecta intención de copia
5. 📖 Activa modo guiado si es necesario

**Para funcionalidad completa:**
- Instala y ejecuta Ollama localmente
- Sube documentos para indexar
- El sistema responderá con evidencia verificable

Documentos indexados: {self.vector_index.count}"""
    
    async def process_message_stream(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """Process message with streaming response.
        
        Yields response tokens and metadata.
        """
        conversation_id = request.conversation_id or str(uuid.uuid4())
        history = self._get_conversation_history(conversation_id)
        
        # Classify intent
        intent = self.intent_classifier.classify(
            request.message,
            history
        )
        
        # Handle smalltalk
        if intent.intent_type == IntentType.SMALLTALK:
            async for token in self.llm.generate_stream(
                request.message,
                context="",
                mode=ResponseMode.CONVERSATIONAL,
                history=history
            ):
                yield token
            return
        
        # Retrieve evidence
        evidence, top_score, _ = await self.retriever.retrieve_with_context(
            request.message,
            history
        )
        
        # Determine mode
        threshold = request.confidence_threshold or LOCAL_CONFIDENCE_THRESHOLD
        has_evidence = top_score >= threshold
        
        if not has_evidence:
            doc_count = self.vector_index.count
            yield INSUFFICIENT_EVIDENCE_MESSAGE['es'].format(
                document_count=doc_count
            )
            return
        
        # Determine response mode
        if ENABLE_ANTI_COPY and self.intent_classifier.should_activate_guided_mode(
            intent, top_score
        ):
            response_mode = ResponseMode.GUIDED_MODE
        else:
            response_mode = intent.recommended_mode
        
        # Format context
        context = self.retriever.format_evidence_context(
            evidence[:5]
        )
        
        # Stream response
        async for token in self.llm.generate_stream(
            request.message,
            context=context,
            mode=response_mode,
            history=history
        ):
            yield token
    
    async def index_document(
        self,
        filename: str,
        content: str
    ) -> dict:
        """Index a new document.
        
        Args:
            filename: Document filename
            content: Document text content
            
        Returns:
            Indexing result with chunk count
        """
        # Chunk the document
        chunks, metadata = self.chunker.chunk_document(
            content, filename
        )
        
        if not chunks:
            return {
                "success": False,
                "error": "No content to index",
                "chunks_added": 0
            }
        
        # Check if embedding service is available
        embedding_available = await self.embedder.check_health()
        
        if not embedding_available:
            # Demo mode: Save chunks without embeddings
            # In production, embeddings are required for semantic search
            logger.warning("Embedding service not available - storing document metadata only")
            return {
                "success": True,
                "filename": filename,
                "chunks_added": 0,
                "total_chunks": len(chunks),
                "demo_mode": True,
                "message": "Documento guardado pero no indexado (Ollama no disponible). Los embeddings se generarán cuando Ollama esté conectado.",
                **metadata
            }
        
        # Generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = await self.embedder.embed_batch(texts)
        
        # Add to index
        added = self.vector_index.add_items(chunks, embeddings)
        
        return {
            "success": True,
            "filename": filename,
            "chunks_added": added,
            "total_chunks": len(chunks),
            **metadata
        }
    
    def get_index_stats(self) -> dict:
        """Get statistics about the document index."""
        return self.vector_index.get_stats()
    
    def clear_index(self):
        """Clear all indexed documents."""
        self.vector_index.clear()
        self.embedder.clear_cache()
    
    def clear_conversation(self, conversation_id: str):
        """Clear a conversation's history."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
