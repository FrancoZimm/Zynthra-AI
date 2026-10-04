import { useState, useEffect, useRef, useCallback } from "react";
import "@/App.css";
import ReactMarkdown from "react-markdown";
import { 
  Send, Upload, FileText, Trash2, AlertTriangle, CheckCircle2,
  BookOpen, Shield, ChevronDown, X, RefreshCw, Loader2,
  MessageCircle, Database, Leaf, Sparkles, GraduationCap,
  Library, Bot, User, FileType, Info, Sliders, Plus,
  HelpCircle, Zap, Target, Download, Copy, Check
} from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ========================================================
// Download Menu — botón con dropdown de formatos
// ========================================================
const DownloadMenu = ({ content }) => {
  const [open, setOpen] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const download = async (format) => {
    setDownloading(true);
    setOpen(false);
    try {
      const res = await axios.post(
        `${API}/export`,
        { content, format, title: "Respuesta Zynthra-AI" },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `zynthra-${Date.now()}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Error al descargar");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        disabled={downloading}
        className="flex items-center gap-1.5 text-xs font-semibold text-[#4A6B2F] hover:text-[#2D3F1F] px-2 py-1 rounded-md hover:bg-[#EEF3DE] transition-colors"
        data-testid="download-button"
      >
        {downloading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
        Descargar
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)}></div>
          <div className="absolute right-0 mt-1 bg-white border border-[#D8D0B8] rounded-md soft-shadow z-20 min-w-[140px] overflow-hidden animate-fadeIn">
            {[
              { fmt: 'pdf', label: 'PDF', desc: '.pdf' },
              { fmt: 'docx', label: 'Word', desc: '.docx' },
              { fmt: 'md', label: 'Markdown', desc: '.md' },
              { fmt: 'txt', label: 'Texto', desc: '.txt' },
            ].map(({ fmt, label, desc }) => (
              <button
                key={fmt}
                onClick={() => download(fmt)}
                className="w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-[#EEF3DE] text-left"
                data-testid={`download-${fmt}`}
              >
                <span className="font-semibold text-[#1F2A1A]">{label}</span>
                <span className="text-[10px] text-[#8A9680] font-mono">{desc}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// ========================================================
// Copy Button
// ========================================================
const CopyButton = ({ content }) => {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button
      onClick={copy}
      className="flex items-center gap-1.5 text-xs font-semibold text-[#4A5A42] hover:text-[#4A6B2F] px-2 py-1 rounded-md hover:bg-[#EEF3DE] transition-colors"
      data-testid="copy-button"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-[#6B9E5C]" /> : <Copy className="w-3.5 h-3.5" />}
      {copied ? "Copiado" : "Copiar"}
    </button>
  );
};

// ========================================================
// Chat Message
// ========================================================
const ChatMessage = ({ message, isUser, evidence, isGuidedMode, responseMode }) => {
  const [showEvidence, setShowEvidence] = useState(false);

  if (isUser) {
    return (
      <div className="flex justify-end mb-5 animate-fadeIn">
        <div className="flex items-start gap-3 max-w-[75%]">
          <div className="natural-card p-4 bg-[#4A6B2F] text-white border-[#4A6B2F]">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-[#4A6B2F] flex items-center justify-center flex-shrink-0 soft-shadow">
            <User className="w-4 h-4 text-white" />
          </div>
        </div>
      </div>
    );
  }

  const bubbleClass = isGuidedMode
    ? "natural-card bg-[#FFF4EC] border-[#B85C3C] border-l-4 border-l-[#B85C3C]"
    : responseMode === "insufficient_evidence"
    ? "natural-card bg-[#FFF9EC] border-[#C48A3C] border-l-4 border-l-[#C48A3C]"
    : "natural-card bg-white border-l-4 border-l-[#6B8E3D]";

  const iconBg = isGuidedMode
    ? "bg-[#B85C3C]"
    : responseMode === "insufficient_evidence"
    ? "bg-[#C48A3C]"
    : "bg-gradient-to-br from-[#6B8E3D] to-[#4A6B2F]";

  const icon = isGuidedMode
    ? <Shield className="w-4 h-4 text-white" />
    : responseMode === "insufficient_evidence"
    ? <AlertTriangle className="w-4 h-4 text-white" />
    : <Sparkles className="w-4 h-4 text-white" />;

  return (
    <div className="flex justify-start mb-5 animate-fadeIn">
      <div className="flex items-start gap-3 max-w-[80%]">
        <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 soft-shadow ${iconBg}`}>
          {icon}
        </div>
        <div className={`p-4 ${bubbleClass}`} data-testid="ai-message">
          {isGuidedMode && (
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[#B85C3C]/20">
              <Shield className="w-4 h-4 text-[#B85C3C]" />
              <span className="text-xs font-bold text-[#B85C3C] uppercase tracking-wide" data-testid="guided-mode-badge">
                Modo Guiado • Anti-copia
              </span>
            </div>
          )}
          {responseMode === "insufficient_evidence" && (
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[#C48A3C]/20">
              <AlertTriangle className="w-4 h-4 text-[#C48A3C]" />
              <span className="text-xs font-bold text-[#C48A3C] uppercase tracking-wide">
                Evidencia Insuficiente
              </span>
            </div>
          )}

          <div className="text-[#1F2A1A] leading-relaxed markdown-body text-sm">
            <ReactMarkdown
              components={{
                h1: ({children}) => <h1 className="text-lg mb-2 mt-3">{children}</h1>,
                h2: ({children}) => <h2 className="text-base mb-2 mt-3">{children}</h2>,
                h3: ({children}) => <h3 className="text-sm mb-1 mt-2">{children}</h3>,
                p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                code: ({inline, children}) => inline ? <code>{children}</code> : <pre><code>{children}</code></pre>,
              }}
            >{message}</ReactMarkdown>
          </div>

          {/* Action buttons: copy + download */}
          <div className="flex items-center gap-1 mt-3 pt-2 border-t border-[#E8E2D0]">
            <CopyButton content={message} />
            <DownloadMenu content={message} />
          </div>

          {evidence && evidence.length > 0 && (
            <div className="mt-3 pt-2 border-t border-[#E8E2D0]">
              <button
                onClick={() => setShowEvidence(!showEvidence)}
                className="flex items-center gap-2 text-xs font-semibold text-[#4A6B2F] hover:text-[#2D3F1F] transition-colors"
                data-testid="toggle-evidence-button"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>{showEvidence ? "Ocultar fuentes" : `Ver ${evidence.length} fuente${evidence.length > 1 ? 's' : ''}`}</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showEvidence ? "rotate-180" : ""}`} />
              </button>
              {showEvidence && (
                <div className="mt-3 space-y-2 animate-fadeIn" data-testid="evidence-panel">
                  {evidence.map((chunk, idx) => (
                    <div key={idx} className="bg-[#EEF3DE] border border-[#D6E2B8] rounded-md p-3" data-testid={`evidence-chunk-${idx}`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-[#4A6B2F]">
                          <FileType className="w-3 h-3" />
                          <span>{chunk.source}</span>
                        </div>
                        <span className="text-[10px] bg-[#4A6B2F] text-white px-2 py-0.5 rounded-full font-semibold">
                          {(chunk.score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <p className="text-xs text-[#4A5A42] leading-relaxed line-clamp-3">{chunk.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ========================================================
// Document Card
// ========================================================
const DocumentCard = ({ doc, onDelete }) => (
  <div className="natural-card p-3 group" data-testid={`document-card-${doc.filename}`}>
    <div className="flex items-start justify-between gap-2">
      <div className="flex items-start gap-2.5 min-w-0 flex-1">
        <div className="w-8 h-8 rounded-md bg-[#EEF3DE] flex items-center justify-center flex-shrink-0">
          <FileType className="w-4 h-4 text-[#4A6B2F]" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-[#1F2A1A] truncate">{doc.filename}</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <div className="w-1.5 h-1.5 rounded-full bg-[#6B8E3D]"></div>
            <p className="text-[11px] text-[#8A9680]">{doc.chunk_count} chunks</p>
          </div>
        </div>
      </div>
      <button
        onClick={() => onDelete(doc.filename)}
        className="p-1.5 text-[#8A9680] hover:text-[#B85C3C] hover:bg-[#FFF4EC] rounded-md transition-all opacity-0 group-hover:opacity-100"
        data-testid={`delete-doc-${doc.filename}`}
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  </div>
);

// ========================================================
// Confidence Slider
// ========================================================
const ConfidenceSlider = ({ value, onChange }) => {
  const level = value < 0.5
    ? { label: "Flexible", color: "text-[#C48A3C]" }
    : value < 0.75
    ? { label: "Balanceado", color: "text-[#4A6B2F]" }
    : { label: "Estricto", color: "text-[#B85C3C]" };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Target className="w-3.5 h-3.5 text-[#4A6B2F]" />
          <label className="text-xs font-semibold text-[#1F2A1A]">Umbral de confianza</label>
        </div>
        <span className={`text-xs font-bold ${level.color}`}>{level.label}</span>
      </div>
      <input
        type="range"
        min="0.3" max="0.9" step="0.05"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        data-testid="confidence-slider"
      />
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-[#8A9680]">30%</span>
        <span className="text-xs font-mono font-bold text-[#4A6B2F]">{(value * 100).toFixed(0)}%</span>
        <span className="text-[10px] text-[#8A9680]">90%</span>
      </div>
    </div>
  );
};

// ========================================================
// Status Item
// ========================================================
const StatusItem = ({ icon: Icon, label, value, active }) => (
  <div className="flex items-center justify-between py-1.5">
    <div className="flex items-center gap-2">
      <Icon className={`w-3.5 h-3.5 ${active ? "text-[#6B9E5C]" : "text-[#C48A3C]"}`} />
      <span className="text-xs text-[#4A5A42]">{label}</span>
    </div>
    <div className="flex items-center gap-1.5">
      <div className={`status-dot ${active ? 'active pulse-indicator' : 'inactive'}`}></div>
      <span className={`text-xs font-semibold ${active ? "text-[#4A6B2F]" : "text-[#C48A3C]"}`}>{value}</span>
    </div>
  </div>
);

// ========================================================
// Main App
// ========================================================
function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [backendOnline, setBackendOnline] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.6);
  const [showSettings, setShowSettings] = useState(false);
  const [uploadText, setUploadText] = useState("");
  const [uploadFilename, setUploadFilename] = useState("");
  const [showUploadModal, setShowUploadModal] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/health`);
      setSystemStatus(res.data);
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
      setSystemStatus(null);
    }
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/documents`);
      setDocuments(res.data);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchDocuments();
    const id = setInterval(fetchStatus, 30000);
    return () => clearInterval(id);
  }, [fetchStatus, fetchDocuments]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;
    const userMessage = inputValue.trim();
    setInputValue("");
    setMessages(prev => [...prev, { content: userMessage, isUser: true }]);
    setIsLoading(true);
    try {
      const res = await axios.post(`${API}/chat`, {
        message: userMessage,
        conversation_id: conversationId,
        include_evidence: true,
        confidence_threshold: confidenceThreshold
      });
      setConversationId(res.data.conversation_id);
      setMessages(prev => [...prev, {
        content: res.data.response,
        isUser: false,
        evidence: res.data.evidence,
        isGuidedMode: res.data.is_guided_mode,
        responseMode: res.data.response_mode,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        content: "Hubo un problema al procesar tu mensaje. Verifica que Ollama esté corriendo.",
        isUser: false,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      setIsLoading(true);
      await axios.post(`${API}/documents/upload-file`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchDocuments();
    } catch { alert("Error al subir archivo"); }
    finally {
      setIsLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleTextUpload = async () => {
    if (!uploadText.trim() || !uploadFilename.trim()) return;
    try {
      setIsLoading(true);
      await axios.post(`${API}/documents/upload`, {
        filename: uploadFilename.endsWith('.txt') ? uploadFilename : `${uploadFilename}.txt`,
        content: uploadText,
        file_type: 'txt'
      });
      fetchDocuments();
      setShowUploadModal(false);
      setUploadText(""); setUploadFilename("");
    } catch { alert("Error al indexar"); }
    finally { setIsLoading(false); }
  };

  const deleteDocument = async (filename) => {
    if (!window.confirm(`¿Eliminar "${filename}"?`)) return;
    try {
      await axios.delete(`${API}/documents/${filename}`);
      fetchDocuments();
    } catch { alert("Error al eliminar"); }
  };

  const exportConversation = async (format) => {
    if (!conversationId) return;
    try {
      const res = await axios.post(
        `${API}/conversations/${conversationId}/export?format=${format}`,
        {},
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `zynthra-conversacion.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch { alert("Error al exportar conversación"); }
  };

  const newConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="min-h-screen flex" data-testid="app-container">
      {/* === Sidebar === */}
      <aside className="w-[320px] bg-[#F3EFE3] border-r border-[#D8D0B8] flex flex-col" data-testid="sidebar">
        <div className="p-5 border-b border-[#D8D0B8]">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#6B8E3D] to-[#4A6B2F] flex items-center justify-center soft-shadow">
              <Sparkles className="w-6 h-6 text-white" strokeWidth={2.2} />
            </div>
            <div>
              <h1 className="text-lg font-bold text-[#1F2A1A] leading-tight tracking-tight">Zynthra-AI</h1>
              <div className="flex items-center gap-1 mt-0.5">
                <Leaf className="w-3 h-3 text-[#6B8E3D]" />
                <p className="text-xs text-[#4A5A42] font-medium">Verificable & Privado</p>
              </div>
            </div>
          </div>
        </div>

        {/* Status */}
        <div className="p-4 border-b border-[#D8D0B8]">
          <div className="natural-card p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#1F2A1A] uppercase tracking-wide">Estado del sistema</span>
              <button onClick={fetchStatus} className="p-1 text-[#8A9680] hover:text-[#4A6B2F] hover:bg-[#EEF3DE] rounded transition-colors" data-testid="refresh-status-button">
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
            <StatusItem icon={Zap} label="Backend" value={backendOnline ? "Online" : "Offline"} active={backendOnline} />
            <StatusItem icon={Bot} label="Motor IA" value={systemStatus?.ollama_available ? "Online" : "Offline"} active={systemStatus?.ollama_available} />
            <StatusItem icon={Library} label="Base de conocimiento" value={`${systemStatus?.documents_indexed || 0} chunks`} active={systemStatus?.documents_indexed > 0} />
            
            {!backendOnline && (
              <div className="mt-3 p-2.5 bg-[#FFF4EC] border border-[#B85C3C]/30 rounded-md">
                <div className="flex items-start gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-[#B85C3C] flex-shrink-0 mt-0.5" />
                  <p className="text-[11px] text-[#B85C3C] leading-relaxed">
                    <strong>Backend no responde.</strong> Verifica que esté corriendo en el puerto 8001.
                  </p>
                </div>
              </div>
            )}
            
            {backendOnline && !systemStatus?.ollama_available && systemStatus?.ollama_error && (
              <div className="mt-3 p-2.5 bg-[#FFF9EC] border border-[#C48A3C]/30 rounded-md">
                <div className="flex items-start gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-[#C48A3C] flex-shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <p className="text-[11px] text-[#1F2A1A] leading-relaxed">
                      <strong>Ollama no accesible</strong>
                    </p>
                    <p className="text-[10px] text-[#4A5A42] mt-0.5 font-mono break-all">
                      {systemStatus.ollama_error}
                    </p>
                    <p className="text-[10px] text-[#8A9680] mt-1">
                      Host: <span className="font-mono">{systemStatus.ollama_host}</span>
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Documents */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="px-4 pt-4 pb-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5">
                <Library className="w-4 h-4 text-[#4A6B2F]" />
                <span className="text-sm font-bold text-[#1F2A1A]">Documentos</span>
                {documents.length > 0 && (
                  <span className="text-[10px] bg-[#4A6B2F] text-white px-1.5 py-0.5 rounded-full font-bold">{documents.length}</span>
                )}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => setShowUploadModal(true)} className="flex items-center justify-center gap-1.5 py-2.5 px-3 bg-[#4A6B2F] text-white text-sm font-semibold rounded-md hover:bg-[#2D3F1F] transition-all soft-shadow" data-testid="upload-text-button">
                <Plus className="w-4 h-4" /> Texto
              </button>
              <label className="flex items-center justify-center gap-1.5 py-2.5 px-3 bg-white border border-[#D8D0B8] text-[#1F2A1A] text-sm font-semibold rounded-md hover:border-[#4A6B2F] hover:bg-[#EEF3DE] cursor-pointer transition-all">
                <Upload className="w-4 h-4" /> Archivo
                <input ref={fileInputRef} type="file" accept=".txt,.md,.pdf,.docx,.xlsx,.xls" onChange={handleFileUpload} className="hidden" data-testid="upload-file-input" />
              </label>
            </div>
            <p className="text-[10px] text-[#8A9680] mt-2 text-center">PDF · DOCX · XLSX · TXT · MD</p>
          </div>

          <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2" data-testid="documents-list">
            {documents.length === 0 ? (
              <div className="text-center py-10 px-4">
                <div className="w-14 h-14 rounded-full bg-[#EEF3DE] flex items-center justify-center mx-auto mb-3">
                  <Database className="w-7 h-7 text-[#6B8E3D]" />
                </div>
                <p className="text-sm font-semibold text-[#1F2A1A] mb-1">Sin documentos aún</p>
                <p className="text-xs text-[#8A9680] leading-relaxed">Sube archivos para crear tu base de conocimiento</p>
              </div>
            ) : (
              documents.map((doc) => <DocumentCard key={doc.id || doc.filename} doc={doc} onDelete={deleteDocument} />)
            )}
          </div>
        </div>

        {/* Settings */}
        <div className="p-4 border-t border-[#D8D0B8] bg-white">
          <button onClick={() => setShowSettings(!showSettings)} className="flex items-center justify-between w-full text-sm font-semibold text-[#1F2A1A] hover:text-[#4A6B2F] transition-colors" data-testid="toggle-settings-button">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4" /> Configuración
            </div>
            <ChevronDown className={`w-4 h-4 transition-transform ${showSettings ? "rotate-180" : ""}`} />
          </button>
          {showSettings && (
            <div className="mt-4 space-y-4 animate-fadeIn" data-testid="settings-panel">
              <ConfidenceSlider value={confidenceThreshold} onChange={setConfidenceThreshold} />
              <div className="pt-3 border-t border-[#E8E2D0] space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#8A9680] flex items-center gap-1"><Bot className="w-3 h-3" /> Modelo LLM</span>
                  <span className="font-mono text-[#1F2A1A] font-semibold">{systemStatus?.model_loaded || "—"}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#8A9680] flex items-center gap-1"><Zap className="w-3 h-3" /> Embeddings</span>
                  <span className="font-mono text-[#1F2A1A] font-semibold">{systemStatus?.embedding_model || "—"}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* === Main === */}
      <main className="flex-1 flex flex-col bg-[#FAF8F1]" data-testid="chat-main">
        <header className="h-16 bg-white border-b border-[#D8D0B8] flex items-center justify-between px-6 soft-shadow">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[#EEF3DE] flex items-center justify-center">
              <MessageCircle className="w-4 h-4 text-[#4A6B2F]" />
            </div>
            <div>
              <p className="text-sm font-bold text-[#1F2A1A]">{conversationId ? "Conversación activa" : "Nueva conversación"}</p>
              {conversationId && <p className="text-[10px] text-[#8A9680] font-mono">ID: {conversationId.slice(0, 8)}</p>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {conversationId && messages.length > 0 && (
              <button
                onClick={() => exportConversation('pdf')}
                className="flex items-center gap-2 text-sm font-semibold text-[#4A6B2F] hover:bg-[#EEF3DE] px-3 py-2 rounded-md transition-all"
                data-testid="export-conversation-button"
              >
                <Download className="w-4 h-4" /> Exportar
              </button>
            )}
            <button onClick={newConversation} className="flex items-center gap-2 text-sm font-semibold text-[#4A6B2F] hover:text-white hover:bg-[#4A6B2F] px-4 py-2 border border-[#4A6B2F] rounded-md transition-all" data-testid="new-conversation-button">
              <Plus className="w-4 h-4" /> Nueva
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6" data-testid="messages-container">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto">
              <div className="relative mb-6">
                <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-[#6B8E3D] to-[#4A6B2F] flex items-center justify-center soft-shadow animate-pop">
                  <Sparkles className="w-12 h-12 text-white" strokeWidth={1.8} />
                </div>
                <div className="absolute -top-2 -right-2 w-9 h-9 rounded-full bg-white border-2 border-[#6B8E3D] flex items-center justify-center soft-shadow">
                  <Leaf className="w-4 h-4 text-[#6B8E3D]" />
                </div>
              </div>
              <h2 className="text-4xl font-bold text-[#1F2A1A] mb-2 tracking-tight">Zynthra-AI</h2>
              <p className="text-base text-[#4A5A42] mb-8 max-w-lg">
                Tu asistente académico con evidencia verificable. Responde con base en tus documentos y te guía para que aprendas de verdad.
              </p>

              <div className="w-full max-w-md">
                <p className="text-xs font-semibold text-[#8A9680] uppercase tracking-wider mb-3">Empieza con una pregunta</p>
                <div className="space-y-2">
                  {[
                    "¿Qué es la fotosíntesis?",
                    "Resúmeme el último documento que subí",
                  ].map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputValue(suggestion)}
                      className="natural-card p-3 w-full text-left hover:border-[#6B8E3D] group flex items-center gap-3"
                      data-testid={`suggestion-${idx}`}
                    >
                      <HelpCircle className="w-4 h-4 text-[#6B8E3D] flex-shrink-0" />
                      <p className="text-sm text-[#1F2A1A] group-hover:text-[#4A6B2F]">{suggestion}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <ChatMessage
                  key={idx}
                  message={msg.content}
                  isUser={msg.isUser}
                  evidence={msg.evidence}
                  isGuidedMode={msg.isGuidedMode}
                  responseMode={msg.responseMode}
                />
              ))}
              {isLoading && (
                <div className="flex justify-start mb-5 animate-fadeIn">
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#6B8E3D] to-[#4A6B2F] flex items-center justify-center flex-shrink-0 soft-shadow">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <div className="natural-card p-4 flex items-center gap-3">
                      <Loader2 className="w-4 h-4 animate-spin text-[#4A6B2F]" />
                      <span className="text-sm text-[#4A5A42]">Pensando...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="px-6 py-4 bg-white border-t border-[#D8D0B8]">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-2 bg-[#F3EFE3] border border-[#D8D0B8] focus-within:border-[#6B8E3D] focus-within:bg-white rounded-xl p-2 transition-all">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Hazme una pregunta..."
                className="flex-1 bg-transparent border-none outline-none px-3 py-2 text-[#1F2A1A] placeholder-[#8A9680]"
                disabled={isLoading}
                data-testid="chat-input"
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputValue.trim()}
                className="px-5 py-2.5 bg-[#4A6B2F] text-white rounded-lg hover:bg-[#2D3F1F] disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center gap-2 font-semibold text-sm soft-shadow"
                data-testid="send-button"
              >
                <Send className="w-4 h-4" /> Enviar
              </button>
            </div>
            <p className="text-[11px] text-[#8A9680] text-center mt-2.5 flex items-center justify-center gap-1.5">
              <Info className="w-3 h-3" />
              Respuestas basadas en tus documentos · Modo guiado anti-copia automático
            </p>
          </div>
        </div>
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-[#1F2A1A]/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn" data-testid="upload-modal">
          <div className="bg-white rounded-xl w-full max-w-lg mx-4 soft-shadow animate-pop">
            <div className="flex items-center justify-between p-5 border-b border-[#E8E2D0]">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-lg bg-[#EEF3DE] flex items-center justify-center">
                  <Plus className="w-5 h-5 text-[#4A6B2F]" />
                </div>
                <h3 className="font-bold text-[#1F2A1A]">Agregar documento</h3>
              </div>
              <button onClick={() => setShowUploadModal(false)} className="p-1.5 text-[#8A9680] hover:text-[#1F2A1A] hover:bg-[#F3EFE3] rounded-md transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-[#1F2A1A] mb-2">Nombre del documento</label>
                <input type="text" value={uploadFilename} onChange={(e) => setUploadFilename(e.target.value)} placeholder="ej: apuntes-fisica" className="w-full px-3 py-2.5" data-testid="upload-filename-input" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-[#1F2A1A] mb-2">Contenido</label>
                <textarea value={uploadText} onChange={(e) => setUploadText(e.target.value)} placeholder="Pega aquí el texto del documento..." rows={10} className="w-full px-3 py-2.5 font-mono text-xs" data-testid="upload-content-input" />
                <p className="text-xs text-[#8A9680] mt-1.5 flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  {uploadText.length} caracteres · aprox. {Math.ceil(uploadText.length / 1100)} chunks
                </p>
              </div>
            </div>
            <div className="p-5 border-t border-[#E8E2D0] flex justify-end gap-2 bg-[#F3EFE3] rounded-b-xl">
              <button onClick={() => setShowUploadModal(false)} className="px-4 py-2 text-sm font-semibold text-[#4A5A42] hover:bg-white rounded-md transition-colors">Cancelar</button>
              <button onClick={handleTextUpload} disabled={!uploadText.trim() || !uploadFilename.trim() || isLoading} className="px-4 py-2 text-sm bg-[#4A6B2F] text-white rounded-md hover:bg-[#2D3F1F] disabled:opacity-40 disabled:cursor-not-allowed font-semibold transition-colors flex items-center gap-2" data-testid="submit-upload-button">
                {isLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Indexando...</> : <><CheckCircle2 className="w-4 h-4" /> Indexar documento</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
