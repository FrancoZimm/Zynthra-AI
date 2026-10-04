# 🎓 Zynthra-AI

> Sistema RAG local educativo con IA pedagógica y protección anti-copia para entornos universitarios.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local-black.svg)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Zynthra-AI** es una aplicación educativa 100% local, privada y gratuita. Usa modelos de lenguaje corriendo en tu máquina (vía Ollama) y un sistema RAG (Retrieval-Augmented Generation) para responder preguntas basándose en tus propios documentos, **con evidencia verificable y protección contra la copia académica**.

---

## ✨ Características principales

| Característica | Descripción |
| --- | --- |
| 🔒 **100% local** | Todo corre en tu máquina. Sin APIs de pago, sin envío de datos a terceros. |
| 📚 **RAG verificable** | Cada respuesta cita las fuentes del documento indexado. |
| 🛡️ **Anti-copia pedagógica** | Detecta intención de copiar y activa automáticamente modo tutor socrático. |
| 🎯 **Detección de intención** | Clasifica mensajes como: estudio legítimo, intento de copia, conversación o clarificación. |
| 📊 **Umbral de confianza configurable** | Controla cuán estricto es el sistema al validar evidencia. |
| 🧠 **Modelos ligeros** | Funciona en PC promedio con Llama 3.2 1B/3B o Qwen2.5 1.5B. |
| 🌐 **Multiidioma** | Prompts optimizados para español e inglés. |
| 💾 **Índice vectorial persistente** | Embeddings guardados en disco, sin rebuild innecesario. |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  - Chat UI con evidencia visible                             │
│  - Panel de documentos                                       │
│  - Configuración de umbrales                                 │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ Intent       │──▶│   RAG        │──▶│   LLM        │    │
│  │ Classifier   │   │  Pipeline    │   │  Service     │    │
│  └──────────────┘   └──────┬───────┘   └──────┬───────┘    │
│                            │                   │            │
│                     ┌──────▼───────┐           │            │
│                     │  Retriever   │           │            │
│                     └──────┬───────┘           │            │
│                            │                   │            │
│                     ┌──────▼───────┐           │            │
│                     │   Indexer    │           │            │
│                     └──────┬───────┘           │            │
│                            │                   │            │
│                     ┌──────▼───────┐           │            │
│                     │  Embeddings  │           │            │
│                     └──────┬───────┘           │            │
└────────────────────────────┼───────────────────┼────────────┘
                             │                   │
                             ▼                   ▼
                    ┌───────────────────────────────┐
                    │         Ollama (Local)        │
                    │  - Embedding model            │
                    │  - Language model             │
                    └───────────────────────────────┘
```

### Módulos del backend

| Módulo | Responsabilidad |
| --- | --- |
| `config/settings.py` | Variables de entorno y constantes |
| `config/prompts.py` | System prompts (RAG, guiado, smalltalk) y patrones de detección |
| `models/schemas.py` | Schemas Pydantic para validación |
| `services/chunking.py` | División de texto con overlap inteligente |
| `services/embeddings.py` | Generación de embeddings vía Ollama (con caché L2-normalizado) |
| `services/indexer.py` | Índice vectorial persistente (JSON gzip + matriz numpy) |
| `services/retriever.py` | Búsqueda semántica con contexto conversacional |
| `services/intent_classifier.py` | Clasificación de intención (copia vs estudio vs conversación) |
| `services/llm_service.py` | Cliente Ollama con soporte streaming |
| `services/rag_pipeline.py` | Orquestador principal de todo el flujo |

---

## 🚀 Instalación rápida

### Prerrequisitos

- **Python 3.11+**
- **Node.js 18+** y **Yarn**
- **MongoDB** (local o remoto)
- **Ollama** ([ollama.com/download](https://ollama.com/download))
- 8 GB RAM mínimo (16 GB recomendado)

### 1. Clonar el repositorio

```bash
git clone https://github.com/FrancoZimm/Zynthra-AI.git
cd Zynthra-AI
```

### 2. Instalar Ollama y descargar modelos

```bash
# Linux / WSL
curl -fsSL https://ollama.com/install.sh | sh

# macOS / Windows: descargar desde https://ollama.com/download

# Descargar modelos ligeros recomendados
ollama pull llama3.2:1b          # LLM (~1.3 GB)
ollama pull nomic-embed-text     # Embeddings (~275 MB)
```

### 3. Configurar backend

```bash
cd backend
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copiar config de ejemplo
cp .env.example .env
# Editar .env si necesitas cambiar puertos/modelos
```

### 4. Configurar frontend

```bash
cd ../frontend
yarn install
cp .env.example .env
```

### 5. Levantar servicios (un solo comando 🚀)

**Opción A — Script automático (más simple):**

```bash
# Linux / macOS
./start.sh

# Windows
start.bat
```

Esto arranca Ollama + Backend + Frontend + MongoDB automáticamente.

**Opción B — Makefile (Linux/macOS):**

```bash
make install   # primera vez
make start     # arrancar todo
make stop      # detener todo
make logs      # ver logs en vivo
```

**Opción C — Docker (sin instalar nada local):**

```bash
docker-compose up -d
```

**Opción D — Manual (4 terminales):**

```bash
# Terminal 1 – MongoDB
mongod --dbpath ./data

# Terminal 2 – Ollama
ollama serve

# Terminal 3 – Backend
cd backend && source venv/bin/activate
uvicorn server:app --reload --port 8001

# Terminal 4 – Frontend
cd frontend && yarn start
```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador. 🎉

---

## 📖 Uso

### 1. Subir documentos

- Click en **Texto** para pegar contenido manualmente.
- Click en **Archivo** para subir `.txt`, `.md` o `.pdf` (próximamente).
- El sistema hace chunking automático, genera embeddings y los indexa.

### 2. Hacer preguntas

- Escribe en el input inferior.
- El sistema:
  1. Clasifica tu intención
  2. Busca evidencia en tus documentos
  3. Decide el modo de respuesta (completa / guiada / evidencia insuficiente)
  4. Genera respuesta citando fuentes

### 3. Ver evidencia

Haz click en **Ver N fuente(s)** bajo cada respuesta para inspeccionar:
- Texto del chunk usado
- Documento de origen
- Puntuación de relevancia (0–100%)

### 4. Ajustar umbral

En **Configuración** (sidebar inferior), arrastra el slider:
- **Permisivo (30%)**: responde aunque haya poca evidencia
- **Estricto (90%)**: solo responde con evidencia muy clara

---

## 🧪 Modo anti-copia en acción

| Usuario escribe | Sistema detecta | Respuesta |
| --- | --- | --- |
| "¿Qué es la fotosíntesis?" | `legitimate_study` | Respuesta completa con evidencia |
| "Hola, ¿qué puedes hacer?" | `smalltalk` | Conversacional, sin RAG |
| "Hazme el ensayo completo sobre X para entregar mañana" | `copy_attempt` | **Modo Guiado**: preguntas socráticas, pide intento del estudiante |
| "Explícame más sobre eso" | `clarification` | Usa contexto de la conversación |

---

## ⚙️ Configuración avanzada

### Cambiar modelo LLM

Edita `backend/.env`:

```env
DEFAULT_LLM_MODEL=qwen2.5:1.5b        # Alternativa más rápida
# o
DEFAULT_LLM_MODEL=llama3.2:3b         # Mayor calidad (requiere 8+ GB RAM)
```

### Ajustar chunking

```env
CHUNK_SIZE_CHARS=1100
CHUNK_OVERLAP_CHARS=150
```

### Umbrales de confianza

```env
LOCAL_CONFIDENCE_THRESHOLD=0.60        # Mínimo para responder
STRONG_LOCAL_CONFIDENCE_THRESHOLD=0.70 # Evidencia sólida
```

### Desactivar anti-copia (modo libre)

```env
ENABLE_ANTI_COPY=false
```

---

## 🔌 Recomendación de modelos

| Modelo | RAM | Velocidad | Calidad | Uso recomendado |
| --- | --- | --- | --- | --- |
| `llama3.2:1b` | 2 GB | ⚡⚡⚡ | ★★☆ | Laptops modestas, demos rápidas |
| `llama3.2:3b` | 4 GB | ⚡⚡ | ★★★ | Balance ideal |
| `qwen2.5:1.5b` | 2 GB | ⚡⚡⚡ | ★★★ | Muy bueno en español |
| `qwen2.5:3b` | 4 GB | ⚡⚡ | ★★★★ | Calidad premium local |
| `nomic-embed-text` | 512 MB | ⚡⚡⚡ | ★★★ | Embeddings recomendados |

---

## 🛣️ Roadmap

- [x] Arquitectura modular profesional
- [x] Sistema RAG con índice persistente
- [x] Clasificación de intención anti-copia
- [x] Modo guiado pedagógico
- [x] UI profesional con evidencia visible
- [ ] Soporte nativo para PDF (PyPDF2 / pdfplumber)
- [ ] Soporte para DOCX (python-docx)
- [ ] OCR de imágenes (EasyOCR)
- [ ] Re-ranking con cross-encoder
- [ ] Chunking semántico (por frases/párrafos)
- [ ] Exportar conversación a PDF/Markdown
- [ ] Perfiles docente vs estudiante
- [ ] Analíticas de uso (dashboard)
- [ ] Tests unitarios y de integración
- [ ] Dockerfile + docker-compose
- [ ] Despliegue en servidor con auth

---

## 📂 Estructura del proyecto

```
zynthra-ai/
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Variables de entorno
│   │   └── prompts.py           # System prompts
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── indexer.py
│   │   ├── retriever.py
│   │   ├── intent_classifier.py
│   │   ├── llm_service.py
│   │   └── rag_pipeline.py
│   ├── documents/               # (auto) Documentos subidos
│   ├── index/                   # (auto) Índice vectorial
│   ├── .env.example
│   ├── requirements.txt
│   └── server.py                # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   ├── package.json
│   └── tailwind.config.js
├── docs/
│   └── ARCHITECTURE.md
├── .gitignore
├── LICENSE
└── README.md
```

---

## 👤 Sobre el proyecto

Este es un **proyecto personal** desarrollado como prueba de concepto de un sistema RAG local educativo, con foco en la verificabilidad y el aprendizaje auténtico (anti-copia pedagógico).

**Objetivos del proyecto:**
- Demostrar un caso de uso real de IA local privada aplicada a educación
- Explorar la combinación de RAG + clasificación de intención + prompts pedagógicos
- Servir como base de portfolio técnico y potencial producto para instituciones educativas

Si te interesa el proyecto, tienes sugerencias, o querés conversar sobre IA educativa, ¡abrí un issue o contáctame!

---

## 🤝 Créditos y herramientas

Diseño del sistema RAG, lógica anti-copia, prompts pedagógicos e integración: **Franco Zimmermann** ([@FrancoZimm](https://github.com/FrancoZimm)).

El scaffolding inicial del frontend se generó con apoyo de herramientas de IA; todo el código se revisó, adaptó y probó a mano.

## 📄 Licencia

MIT © 2026 — Ver archivo [LICENSE](LICENSE)

---

## 💡 Filosofía

> "El objetivo no es que la IA haga la tarea por el estudiante, sino que ayude al estudiante a aprender de verdad."

Este proyecto se basa en tres principios:

1. **Verificable**: Cada respuesta cita evidencia inspeccionable.
2. **Pedagógico**: Prioriza comprensión sobre entrega.
3. **Privado**: Todo local, sin costos, sin telemetría.

---

**¿Preguntas? ¿Ideas?** Abre un issue o contáctame.
