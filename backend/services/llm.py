"""LLM service for text generation via Ollama.

Handles communication with Ollama for text generation.
"""
import httpx
import json
import logging
from typing import List, Optional, AsyncGenerator

from config.settings import (
    OLLAMA_HOST,
    DEFAULT_LLM_MODEL,
    OLLAMA_TIMEOUT
)
from config.prompts import (
    RAG_SYSTEM_PROMPT,
    SMALLTALK_SYSTEM_PROMPT,
    GUIDED_MODE_PROMPT
)
from models.schemas import ResponseMode

logger = logging.getLogger(__name__)


class LLM:
    """Wrapper around Ollama chat API with streaming support."""
    
    def __init__(
        self,
        model: str = DEFAULT_LLM_MODEL,
        host: str = OLLAMA_HOST
    ):
        self.model = model
        self.host = host
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
    
    def _get_system_prompt(self, mode: ResponseMode) -> str:
        """Get appropriate system prompt for response mode."""
        if mode == ResponseMode.GUIDED_MODE:
            return GUIDED_MODE_PROMPT
        elif mode == ResponseMode.CONVERSATIONAL:
            return SMALLTALK_SYSTEM_PROMPT
        else:
            return RAG_SYSTEM_PROMPT
    
    def _build_messages(
        self,
        user_message: str,
        context: str,
        mode: ResponseMode,
        history: Optional[List[dict]] = None
    ) -> List[dict]:
        """Build messages array for chat API.
        
        Args:
            user_message: Current user message
            context: Retrieved RAG context
            mode: Response mode
            history: Conversation history
            
        Returns:
            List of message dicts for Ollama chat API
        """
        messages = []
        
        # System message
        system_prompt = self._get_system_prompt(mode)
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        if history:
            for msg in history[-6:]:  # Last 6 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Build user message with context
        if context and mode != ResponseMode.CONVERSATIONAL:
            full_message = f"""CONTEXTO RECUPERADO (usa esta información para responder):
{context}

---

PREGUNTA DEL USUARIO:
{user_message}"""
        else:
            full_message = user_message
        
        messages.append({"role": "user", "content": full_message})
        
        return messages
    
    async def generate(
        self,
        user_message: str,
        context: str = "",
        mode: ResponseMode = ResponseMode.FULL_RESPONSE,
        history: Optional[List[dict]] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate response using Ollama chat API.
        
        Args:
            user_message: User's message
            context: RAG context
            mode: Response mode
            history: Conversation history
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        messages = self._build_messages(
            user_message, context, mode, history
        )
        
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_ctx": 4096
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return result["message"]["content"]
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        user_message: str,
        context: str = "",
        mode: ResponseMode = ResponseMode.FULL_RESPONSE,
        history: Optional[List[dict]] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Generate response with streaming.
        
        Args:
            user_message: User's message
            context: RAG context
            mode: Response mode
            history: Conversation history
            temperature: Sampling temperature
            
        Yields:
            Response tokens as they are generated
        """
        messages = self._build_messages(
            user_message, context, mode, history
        )
        
        try:
            client = await self._get_client()
            async with client.stream(
                "POST",
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_ctx": 4096
                    }
                },
                timeout=OLLAMA_TIMEOUT
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if content := data.get("message", {}).get("content"):
                            yield content
                        if data.get("done"):
                            break
                            
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"Error: {str(e)}"
    
    async def check_health(self) -> tuple[bool, str]:
        """Check if LLM service is available.
        
        Returns:
            Tuple of (is_healthy, error_message)
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                return True, ""
            return False, f"HTTP {response.status_code} from {self.host}"
        except httpx.ConnectError as e:
            msg = f"No se pudo conectar a Ollama en {self.host}. ¿Está corriendo 'ollama serve'?"
            logger.warning(msg)
            return False, msg
        except httpx.TimeoutException:
            msg = f"Timeout conectando a Ollama en {self.host}"
            logger.warning(msg)
            return False, msg
        except Exception as e:
            msg = f"Error consultando Ollama: {type(e).__name__}: {e}"
            logger.warning(msg)
            return False, msg
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.host}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []
