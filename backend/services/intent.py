"""Intent classification service for anti-copy detection.

Classifies user intent to determine appropriate response mode.
"""
from typing import List, Tuple
import re
import logging

from config.prompts import COPY_INTENT_PATTERNS, LEGITIMATE_STUDY_PATTERNS
from models.schemas import IntentClassification, IntentType, ResponseMode

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Service for classifying user intent."""
    
    def __init__(self):
        self.copy_patterns = COPY_INTENT_PATTERNS
        self.legitimate_patterns = LEGITIMATE_STUDY_PATTERNS
        self.smalltalk_patterns = self._build_smalltalk_patterns()
    
    def _build_smalltalk_patterns(self) -> dict:
        """Build patterns for smalltalk detection."""
        return {
            'es': [
                'hola', 'buenos días', 'buenas tardes', 'buenas noches',
                'gracias', 'muchas gracias', 'adiós', 'hasta luego',
                'cómo estás', 'qué tal', 'quién eres', 'cuál es tu nombre',
                'ok', 'vale', 'entendido', 'perfecto', 'genial'
            ],
            'en': [
                'hello', 'hi', 'good morning', 'good afternoon', 'good evening',
                'thanks', 'thank you', 'goodbye', 'bye', 'see you',
                'how are you', "what's up", 'who are you', 'what is your name',
                'ok', 'okay', 'got it', 'perfect', 'great'
            ]
        }
    
    def classify(
        self,
        message: str,
        conversation_history: List[dict] = None
    ) -> IntentClassification:
        """Classify user message intent.
        
        Args:
            message: User message
            conversation_history: Previous messages for context
            
        Returns:
            IntentClassification with type, confidence, and recommended mode
        """
        message_lower = message.lower().strip()
        
        # Check for smalltalk first (highest priority for short messages)
        if self._is_smalltalk(message_lower):
            return IntentClassification(
                intent_type=IntentType.SMALLTALK,
                confidence=0.9,
                triggered_patterns=[],
                recommended_mode=ResponseMode.CONVERSATIONAL
            )
        
        # Check for copy intent
        copy_score, copy_patterns = self._check_copy_intent(message_lower)
        
        # Check for legitimate study intent
        study_score, study_patterns = self._check_study_intent(message_lower)
        
        # Determine intent based on scores
        if copy_score > 0.6 and copy_score > study_score:
            return IntentClassification(
                intent_type=IntentType.COPY_ATTEMPT,
                confidence=copy_score,
                triggered_patterns=copy_patterns,
                recommended_mode=ResponseMode.GUIDED_MODE
            )
        
        if study_score > 0.5:
            return IntentClassification(
                intent_type=IntentType.LEGITIMATE_STUDY,
                confidence=study_score,
                triggered_patterns=study_patterns,
                recommended_mode=ResponseMode.FULL_RESPONSE
            )
        
        # Check for clarification (follow-up questions)
        if self._is_clarification(message_lower, conversation_history):
            return IntentClassification(
                intent_type=IntentType.CLARIFICATION,
                confidence=0.7,
                triggered_patterns=[],
                recommended_mode=ResponseMode.FULL_RESPONSE
            )
        
        # Default: unknown but allow full response
        return IntentClassification(
            intent_type=IntentType.UNKNOWN,
            confidence=0.5,
            triggered_patterns=[],
            recommended_mode=ResponseMode.FULL_RESPONSE
        )
    
    def _is_smalltalk(self, message: str) -> bool:
        """Check if message is casual conversation."""
        # Very short messages are likely smalltalk
        if len(message.split()) <= 3:
            for lang_patterns in self.smalltalk_patterns.values():
                for pattern in lang_patterns:
                    if pattern in message or message in pattern:
                        return True
        return False
    
    def _check_copy_intent(self, message: str) -> Tuple[float, List[str]]:
        """Check for copy/cheating intent.
        
        Returns:
            Tuple of (confidence score, matched patterns)
        """
        matched = []
        
        for lang, patterns in self.copy_patterns.items():
            for pattern in patterns:
                if pattern in message:
                    matched.append(pattern)
        
        # Additional heuristics
        # Long messages asking for complete solutions
        if len(message.split()) > 20 and any(w in message for w in ['completo', 'complete', 'todo', 'all', 'entero']):
            matched.append('long_complete_request')
        
        # Direct assignment language
        assignment_words = ['tarea', 'homework', 'assignment', 'trabajo', 'ensayo', 'essay', 'examen', 'exam']
        if any(word in message for word in assignment_words):
            if any(verb in message for verb in ['haz', 'hazme', 'escribe', 'resuelve', 'do', 'write', 'solve']):
                matched.append('assignment_delegation')
        
        if not matched:
            return 0.0, []
        
        # Calculate confidence based on number and type of matches
        confidence = min(0.3 + (len(matched) * 0.15), 0.95)
        return confidence, matched
    
    def _check_study_intent(self, message: str) -> Tuple[float, List[str]]:
        """Check for legitimate study intent.
        
        Returns:
            Tuple of (confidence score, matched patterns)
        """
        matched = []
        
        for lang, patterns in self.legitimate_patterns.items():
            for pattern in patterns:
                if pattern in message:
                    matched.append(pattern)
        
        # Question words indicate learning intent
        question_words = ['qué', 'cómo', 'por qué', 'cuál', 'cuándo', 'what', 'how', 'why', 'which', 'when']
        if any(word in message for word in question_words):
            matched.append('question_word')
        
        if not matched:
            return 0.0, []
        
        confidence = min(0.4 + (len(matched) * 0.15), 0.95)
        return confidence, matched
    
    def _is_clarification(self, message: str, history: List[dict] = None) -> bool:
        """Check if message is a follow-up clarification."""
        if not history:
            return False
        
        clarification_indicators = [
            '¿y', 'pero', 'entonces', 'es decir', 'o sea',
            'and', 'but', 'so', 'meaning', 'in other words',
            '¿qué quieres decir', 'what do you mean',
            'más detalles', 'more details', 'explícame más'
        ]
        
        return any(ind in message for ind in clarification_indicators)
    
    def should_activate_guided_mode(
        self,
        intent: IntentClassification,
        evidence_score: float
    ) -> bool:
        """Determine if guided mode should be activated.
        
        Considers both intent classification and evidence availability.
        
        Args:
            intent: Classified intent
            evidence_score: Top score from evidence retrieval
            
        Returns:
            True if guided mode should be activated
        """
        # Always activate for clear copy attempts
        if intent.intent_type == IntentType.COPY_ATTEMPT and intent.confidence > 0.7:
            return True
        
        # Don't activate for smalltalk or clear study intent
        if intent.intent_type in [IntentType.SMALLTALK, IntentType.LEGITIMATE_STUDY]:
            return False
        
        # For unknown intent with high-scoring evidence (likely evaluable content)
        if intent.intent_type == IntentType.UNKNOWN and evidence_score > 0.8:
            return True
        
        return False
