"""Zynthra-AI - Main FastAPI Application.

A local, verifiable, pedagogical AI tutor with RAG capabilities
and anti-copy protection for educational environments.
"""
from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
import logging
import io
import uuid
from datetime import datetime, timezone

# Load environment before importing config
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from config.settings import (
    MONGO_URL, DB_NAME, CORS_ORIGINS,
    OLLAMA_HOST, DEFAULT_LLM_MODEL, DEFAULT_EMBEDDING_MODEL,
    LOCAL_CONFIDENCE_THRESHOLD, DOCS_DIR
)
from models.schemas import (
    ChatRequest, ChatResponse, DocumentUpload, Document,
    SystemStatus, EvidenceChunk
)
from services import ZynthraCore, DocumentReader, DocumentExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
zynthra: Optional[ZynthraCore] = None
db_client: Optional[AsyncIOMotorClient] = None
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global zynthra, db_client, db
    
    logger.info("Starting Zynthra-AI...")
    
    # MongoDB (optional — app works without it)
    try:
        db_client = AsyncIOMotorClient(
            MONGO_URL,
            serverSelectionTimeoutMS=2000
        )
        # Ping to verify connection
        await db_client.admin.command('ping')
        db = db_client[DB_NAME]
        logger.info(f"Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        logger.warning(
            f"MongoDB no disponible ({e}). "
            "La app funcionará sin persistencia de logs."
        )
        db_client = None
        db = None
    
    # Core orchestrator
    zynthra = ZynthraCore()
    logger.info("Zynthra core initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if zynthra:
        await zynthra.close()
    if db_client:
        db_client.close()


app = FastAPI(
    title="Zynthra-AI",
    description="Sistema RAG educativo local con protección anti-copia",
    version="1.0.0",
    lifespan=lifespan
)

api_router = APIRouter(prefix="/api")


async def safe_db_insert(collection_name: str, doc: dict):
    """Insert into DB if available, else silently ignore."""
    if db is not None:
        try:
            await db[collection_name].insert_one(doc)
        except Exception as e:
            logger.warning(f"DB insert failed on {collection_name}: {e}")


async def safe_db_find(collection_name: str, query: dict = None, projection: dict = None, limit: int = 100):
    """Find from DB if available, else return empty list."""
    if db is None:
        return []
    try:
        cursor = db[collection_name].find(query or {}, projection or {"_id": 0})
        return await cursor.to_list(limit)
    except Exception as e:
        logger.warning(f"DB find failed on {collection_name}: {e}")
        return []


async def safe_db_delete(collection_name: str, query: dict):
    """Delete from DB if available."""
    if db is not None:
        try:
            await db[collection_name].delete_one(query)
        except Exception as e:
            logger.warning(f"DB delete failed on {collection_name}: {e}")


# =========================================================
# Health & Status
# =========================================================

@api_router.get("/")
async def root():
    return {"message": "Zynthra-AI API", "version": "1.0.0", "status": "operational"}


@api_router.get("/health", response_model=SystemStatus)
async def health_check():
    """Check system health and component status."""
    try:
        ollama_ok = False
        ollama_error = ""
        if zynthra:
            ollama_ok, ollama_error = await zynthra.llm.check_health()
        index_stats = zynthra.get_index_stats() if zynthra else {}
        
        return SystemStatus(
            status="healthy" if ollama_ok else "degraded",
            ollama_available=ollama_ok,
            ollama_error=ollama_error,
            ollama_host=zynthra.llm.host if zynthra else "",
            documents_indexed=index_stats.get('total_items', 0),
            model_loaded=DEFAULT_LLM_MODEL,
            embedding_model=DEFAULT_EMBEDDING_MODEL,
            memory_usage_mb=0.0
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemStatus(
            status="unhealthy",
            ollama_available=False,
            ollama_error=str(e),
            documents_indexed=0,
            model_loaded="",
            embedding_model=""
        )


@api_router.get("/config")
async def get_config():
    return {
        "llm_model": DEFAULT_LLM_MODEL,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "confidence_threshold": LOCAL_CONFIDENCE_THRESHOLD,
        "ollama_host": OLLAMA_HOST
    }


# =========================================================
# Chat & RAG
# =========================================================

@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the Zynthra pipeline."""
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    
    try:
        response = await zynthra.process_message(request)
        
        await safe_db_insert("chat_logs", {
            "conversation_id": response.conversation_id,
            "user_message": request.message,
            "response_mode": response.response_mode.value,
            "confidence_score": response.confidence_score,
            "is_guided_mode": response.is_guided_mode,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return response
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response tokens."""
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    
    async def generate():
        try:
            async for token in zynthra.process_message_stream(request):
                yield token
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Error: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# =========================================================
# Documents
# =========================================================

@api_router.post("/documents/upload")
async def upload_document(doc: DocumentUpload):
    """Upload text content as a document."""
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    
    try:
        doc_path = DOCS_DIR / doc.filename
        doc_path.write_text(doc.content, encoding='utf-8')
        
        result = await zynthra.index_document(doc.filename, doc.content)
        
        doc_record = {
            "id": str(uuid.uuid4()),
            "filename": doc.filename,
            "content_preview": doc.content[:200] if len(doc.content) > 200 else doc.content,
            "chunk_count": result.get('chunks_added', 0),
            "file_size": len(doc.content.encode('utf-8')),
            "file_type": doc.file_type,
            "indexed_at": datetime.now(timezone.utc).isoformat()
        }
        await safe_db_insert("documents", doc_record)
        
        return {"success": True, "message": f"Documento '{doc.filename}' indexado", **result}
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/documents/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file (TXT, MD, PDF, DOCX, XLSX)."""
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    
    if not DocumentReader.is_supported(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Permitidos: {', '.join(sorted(DocumentReader.SUPPORTED_EXTENSIONS))}"
        )
    
    try:
        content = await file.read()
        text_content = DocumentReader.parse(content, file.filename)
        
        if not text_content or not text_content.strip():
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del archivo")
        
        base_name = Path(file.filename).stem
        doc_path = DOCS_DIR / f"{base_name}.txt"
        doc_path.write_text(text_content, encoding='utf-8')
        
        result = await zynthra.index_document(file.filename, text_content)
        
        doc_record = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "content_preview": text_content[:200],
            "chunk_count": result.get('chunks_added', 0),
            "file_size": len(content),
            "file_type": file.filename.split('.')[-1] if '.' in file.filename else 'txt',
            "indexed_at": datetime.now(timezone.utc).isoformat()
        }
        await safe_db_insert("documents", doc_record)
        
        return {"success": True, "message": f"Archivo '{file.filename}' indexado", **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/documents", response_model=List[Document])
async def list_documents():
    try:
        docs = await safe_db_find("documents")
        return docs
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/documents/{filename}")
async def delete_document(filename: str):
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    
    try:
        removed = zynthra.vector_index.remove_by_source(filename)
        await safe_db_delete("documents", {"filename": filename})
        doc_path = DOCS_DIR / filename
        if doc_path.exists():
            doc_path.unlink()
        return {"success": True, "message": f"Documento '{filename}' eliminado", "chunks_removed": removed}
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/documents/stats")
async def document_stats():
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    return zynthra.get_index_stats()


# =========================================================
# Export / Download
# =========================================================

class ExportRequest(BaseModel):
    """Request to export content as a downloadable document."""
    content: str
    format: str = "pdf"  # pdf, docx, txt, md
    title: Optional[str] = None
    filename: Optional[str] = None


@api_router.post("/export")
async def export_document(request: ExportRequest):
    """Generate a downloadable document from content."""
    try:
        metadata = {
            "Generado": datetime.now().strftime('%d/%m/%Y %H:%M'),
            "Por": "Zynthra-AI"
        }
        
        file_bytes = DocumentExporter.export(
            content=request.content,
            format=request.format,
            title=request.title or "Documento Zynthra-AI",
            metadata=metadata
        )
        
        base_name = request.filename or f"zynthra-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        filename = f"{base_name}.{request.format.lower()}"
        mime = DocumentExporter.get_mime_type(request.format)
        
        return Response(
            content=file_bytes,
            media_type=mime,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(file_bytes))
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str, format: str = "pdf"):
    """Export a full conversation as a downloadable document."""
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    
    try:
        messages = zynthra._get_conversation_history(conversation_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Conversación no encontrada o vacía")
        
        file_bytes = DocumentExporter.export_conversation(
            messages=messages,
            format=format,
            title=f"Conversación Zynthra-AI"
        )
        
        filename = f"zynthra-conversacion-{conversation_id[:8]}.{format.lower()}"
        mime = DocumentExporter.get_mime_type(format)
        
        return Response(
            content=file_bytes,
            media_type=mime,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# Conversations
# =========================================================

@api_router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    zynthra.clear_conversation(conversation_id)
    return {"success": True, "message": "Conversación eliminada"}


@api_router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    history = zynthra._get_conversation_history(conversation_id)
    return {"conversation_id": conversation_id, "messages": history}


# =========================================================
# Models
# =========================================================

@api_router.get("/models")
async def list_models():
    if not zynthra:
        raise HTTPException(status_code=503, detail="Zynthra not initialized")
    try:
        models = await zynthra.llm.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"List models error: {e}")
        return {"models": [], "error": str(e)}


# Register router & middleware
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
