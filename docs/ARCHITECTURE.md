# Arquitectura – Zynthra-AI

Documento técnico sobre el diseño del sistema.

## 1. Visión general

Zynthra-AI es una aplicación full-stack local que combina:

- **Frontend React** (UI conversacional con panel de evidencia)
- **Backend FastAPI** (orquestador del pipeline RAG)
- **Ollama** (motor de inferencia local)
- **MongoDB** (persistencia de conversaciones y metadatos)
- **Índice vectorial propio** (JSON gzip + numpy para búsqueda por similitud)

Todo el procesamiento ocurre en la máquina del usuario. No hay llamadas a APIs externas.

## 2. Flujo end-to-end

```
Usuario escribe mensaje
        │
        ▼
┌──────────────────────────────────────┐
│ 1. IntentClassifier                  │
│    - Smalltalk? → respuesta directa  │
│    - Copia?     → modo guiado        │
│    - Estudio?   → RAG completo       │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ 2. RetrievalService                  │
│    - Embed query                     │
│    - Dot product vs índice           │
│    - Top-K chunks                    │
│    - Chequeo de umbral               │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ 3. Decision gate                     │
│    - ¿Evidencia suficiente?          │
│    - ¿Activar modo guiado?           │
└──────────────────┬───────────────────┘
                   ▼
┌──────────────────────────────────────┐
│ 4. LLMService                        │
│    - System prompt según modo        │
│    - Contexto = chunks recuperados   │
│    - Historial conversacional        │
│    - Ollama chat API                 │
└──────────────────┬───────────────────┘
                   ▼
        Respuesta + evidencia
```

## 3. Pipeline de indexación

```
Documento
    │
    ▼
[ChunkingService]
    - Sliding window 1100 chars / overlap 150
    - Corte en frontera de oración si es posible
    │
    ▼
[EmbeddingService]
    - Ollama /api/embed (batch)
    - L2 normalize → vectores unitarios
    - Cache en memoria
    │
    ▼
[IndexService]
    - Deduplicación por chunk_id (hash de contenido)
    - Persistencia: JSON + gzip
    - Matriz numpy float32 en RAM para búsqueda rápida
```

## 4. Búsqueda semántica

Dado que los embeddings están L2-normalizados, la **similitud coseno es equivalente al producto punto**. Esto permite:

```python
scores = embeddings_matrix @ query_embedding   # una sola multiplicación matricial
top_k = np.argsort(scores)[::-1][:k]
```

Complejidad: **O(N·d)** donde N = chunks, d = dimensión embedding (~768).

Para <10 000 chunks esto es trivial (< 5 ms). Para escalar a millones, considerar FAISS/Qdrant.

## 5. Clasificación de intención

El `IntentClassifier` usa un enfoque **híbrido basado en reglas + heurísticas**:

1. **Patrones léxicos** (multi-idioma): listas curadas de frases asociadas a cada intención.
2. **Heurísticas estructurales**:
   - Mensajes cortos (<3 palabras) → posible smalltalk
   - Presencia de verbo imperativo + sustantivo académico → posible copia
   - Palabras interrogativas → intención de estudio
3. **Contexto conversacional**: indicadores de seguimiento ("eso", "entonces", "y qué más")

Se prefirió este enfoque sobre un clasificador ML porque:
- No requiere training data
- Es interpretable (se ven los patrones que dispararon)
- Es rápido (< 1 ms)
- Fácil de extender con nuevos patrones

**Futuro**: añadir clasificador fine-tuneado si los patrones resultan insuficientes.

## 6. Modo guiado (anti-copia)

Cuando `intent == COPY_ATTEMPT` con confianza > 0.7:

1. Se reemplaza el system prompt por `GUIDED_MODE_PROMPT`
2. El LLM recibe instrucciones estrictas de **no dar la respuesta directa**
3. Se usa método socrático: preguntas, pistas, división en pasos
4. La UI muestra banner rojo indicando modo activo

Esto es un **gate a nivel de prompt**, no bloqueo del modelo. El estudiante **sí puede** obtener ayuda — pero gradual y condicionada a que muestre esfuerzo.

## 7. Gestión de contexto conversacional

- Últimos 20 mensajes por conversación en memoria
- Los últimos 6 mensajes se pasan al LLM como historial
- Para preguntas de seguimiento ("y por qué?"), se construye query contextual concatenando las últimas 2 preguntas del usuario antes de hacer retrieval

## 8. Decisiones técnicas justificadas

| Decisión | Razón |
| --- | --- |
| **JSON gzip** para índice (en vez de FAISS/Chroma) | Cero dependencias pesadas, portable, suficiente para <10k chunks |
| **Numpy** para búsqueda | Ya es dependencia, rápido, simple |
| **Ollama** sobre llama.cpp directo | API HTTP estable, gestión de modelos, streaming nativo |
| **Dot product** (no cosine explícito) | Equivalente para vectores L2-norm, más eficiente |
| **Rules-based intent** (no ML) | Interpretable, sin training, extensible |
| **MongoDB** para logs | Schema-flexible, ideal para analytics posteriores |
| **Modo demo** cuando Ollama no disponible | Permite exhibir la app sin requerir setup completo |

## 9. Puntos de extensión

- **Parsers**: `services/parsers/` para PDF, DOCX, imágenes (OCR)
- **Rerankers**: `services/reranker.py` con cross-encoder opcional
- **Auth**: middleware FastAPI con JWT + perfiles docente/estudiante
- **Analytics**: colección MongoDB `chat_logs` ya captura modo, score, intención
- **Fine-tuning**: exportar conversaciones marcadas por docente como dataset

## 10. Limitaciones actuales

1. Chunks puramente por caracteres (no semánticos) — puede cortar frases
2. Sin re-ranking — top-K directo de similarity search
3. Sin detección de contradicciones entre documentos
4. Memoria conversacional en RAM (se pierde al reiniciar backend)
5. Sin autenticación — pensado para uso local/controlado

Ver `README.md` sección **Roadmap** para planes futuros.
