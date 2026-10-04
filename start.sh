#!/bin/bash
# =====================================================
# Zynthra-AI - START ALL (Linux/macOS)
# =====================================================
# Arranca Ollama + Backend + Frontend con un solo comando
# Uso: ./start.sh
# Detener todo: Ctrl+C

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  Zynthra-AI - Iniciando servicios  ${NC}"
echo -e "${BLUE}===============================================${NC}\n"

# --- Verificar prerrequisitos ---
command -v ollama >/dev/null 2>&1 || { echo -e "${RED}X Ollama no instalado. Instala desde https://ollama.com${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}X Python 3 no instalado${NC}"; exit 1; }
command -v yarn >/dev/null 2>&1 || { echo -e "${RED}X Yarn no instalado${NC}"; exit 1; }

# --- Crear directorio de logs ---
mkdir -p logs

# --- Función para cerrar procesos al salir ---
cleanup() {
    echo -e "\n${YELLOW}Deteniendo servicios...${NC}"
    [ -n "$OLLAMA_PID" ] && kill $OLLAMA_PID 2>/dev/null && echo -e "  ${GREEN}✓ Ollama detenido${NC}"
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null && echo -e "  ${GREEN}✓ Backend detenido${NC}"
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null && echo -e "  ${GREEN}✓ Frontend detenido${NC}"
    [ -n "$MONGO_PID" ] && kill $MONGO_PID 2>/dev/null && echo -e "  ${GREEN}✓ MongoDB detenido${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- 1. MongoDB (solo si no corre como servicio) ---
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}[1/4] Iniciando MongoDB...${NC}"
    mkdir -p data/db
    mongod --dbpath ./data/db --logpath ./logs/mongodb.log --fork >/dev/null 2>&1 || {
        echo -e "${RED}  ! MongoDB no pudo iniciar. ¿Está instalado? Corriendo sin MongoDB local...${NC}"
    }
    echo -e "${GREEN}  ✓ MongoDB corriendo en :27017${NC}"
else
    echo -e "${GREEN}[1/4] MongoDB ya corriendo${NC}"
fi

# --- 2. Ollama ---
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${YELLOW}[2/4] Iniciando Ollama...${NC}"
    ollama serve > logs/ollama.log 2>&1 &
    OLLAMA_PID=$!
    sleep 3
    echo -e "${GREEN}  ✓ Ollama corriendo en :11434 (PID $OLLAMA_PID)${NC}"
else
    echo -e "${GREEN}[2/4] Ollama ya corriendo${NC}"
fi

# --- 3. Backend ---
echo -e "${YELLOW}[3/4] Iniciando Backend FastAPI...${NC}"
cd backend
[ ! -d "venv" ] && { echo -e "${RED}  X Primero corre: ./setup.sh${NC}"; exit 1; }
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 4
echo -e "${GREEN}  ✓ Backend corriendo en :8001 (PID $BACKEND_PID)${NC}"

# --- 4. Frontend ---
echo -e "${YELLOW}[4/4] Iniciando Frontend React...${NC}"
cd frontend
[ ! -d "node_modules" ] && { echo -e "${RED}  X Primero corre: ./setup.sh${NC}"; exit 1; }
BROWSER=none yarn start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 5
echo -e "${GREEN}  ✓ Frontend corriendo en :3000 (PID $FRONTEND_PID)${NC}"

# --- Listo ---
echo -e "\n${BLUE}===============================================${NC}"
echo -e "${GREEN}  ✓ Todo listo. Abre http://localhost:3000${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "\n${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f logs/backend.log"
echo -e "  Frontend: tail -f logs/frontend.log"
echo -e "  Ollama:   tail -f logs/ollama.log"
echo -e "\n${YELLOW}Para detener todo:${NC} Ctrl+C\n"

# Mantener script vivo y mostrar logs combinados
tail -f logs/backend.log logs/frontend.log 2>/dev/null
