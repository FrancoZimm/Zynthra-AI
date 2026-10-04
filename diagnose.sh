#!/bin/bash
# =====================================================
# Zynthra-AI - Script de Diagnóstico (Linux/macOS)
# =====================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  Zynthra-AI - Diagnóstico del sistema        ${NC}"
echo -e "${BLUE}===============================================${NC}\n"

# 1. Ollama en 127.0.0.1
echo -e "${YELLOW}[1/5] Verificando Ollama en 127.0.0.1:11434...${NC}"
if curl -s --connect-timeout 3 http://127.0.0.1:11434/api/tags >/dev/null; then
    echo -e "  ${GREEN}✓ Ollama responde correctamente${NC}"
    echo ""
    echo "  Modelos disponibles:"
    curl -s http://127.0.0.1:11434/api/tags | python3 -c "import json,sys;d=json.load(sys.stdin);[print(f'    • {m[\"name\"]} ({m[\"size\"]//(1024*1024)} MB)') for m in d.get('models',[])]" 2>/dev/null || echo "    (no se pudo parsear)"
else
    echo -e "  ${RED}✗ Ollama NO responde en 127.0.0.1:11434${NC}"
    echo "     - Verifica que 'ollama serve' esté corriendo"
    echo "     - Prueba: ollama list"
fi
echo ""

# 2. Backend
echo -e "${YELLOW}[2/5] Verificando Backend FastAPI en puerto 8001...${NC}"
if curl -s --connect-timeout 3 http://127.0.0.1:8001/api/health >/dev/null; then
    echo -e "  ${GREEN}✓ Backend FastAPI responde${NC}"
    echo ""
    echo "  Respuesta /api/health:"
    curl -s http://127.0.0.1:8001/api/health | python3 -m json.tool 2>/dev/null || curl -s http://127.0.0.1:8001/api/health
else
    echo -e "  ${RED}✗ Backend NO responde en puerto 8001${NC}"
    echo "     - Corre: cd backend && source venv/bin/activate && uvicorn server:app --reload --port 8001"
fi
echo ""

# 3. Frontend
echo -e "${YELLOW}[3/5] Verificando Frontend en puerto 3000...${NC}"
if curl -s --connect-timeout 3 http://127.0.0.1:3000 >/dev/null; then
    echo -e "  ${GREEN}✓ Frontend React responde${NC}"
else
    echo -e "  ${RED}✗ Frontend NO responde en puerto 3000${NC}"
    echo "     - Corre: cd frontend && yarn start"
fi
echo ""

# 4. MongoDB
echo -e "${YELLOW}[4/5] Verificando MongoDB en puerto 27017...${NC}"
if nc -z 127.0.0.1 27017 2>/dev/null || (netstat -ln 2>/dev/null | grep -q ":27017.*LISTEN"); then
    echo -e "  ${GREEN}✓ MongoDB escucha en puerto 27017${NC}"
else
    echo -e "  ${YELLOW}! MongoDB NO parece estar corriendo${NC}"
    echo "     - Si lo necesitas: mongod --dbpath ./data/db"
fi
echo ""

# 5. .env config
echo -e "${YELLOW}[5/5] Verificando configuración backend/.env...${NC}"
if [ -f "backend/.env" ]; then
    OLLAMA_HOST_CFG=$(grep "^OLLAMA_HOST=" backend/.env | cut -d'=' -f2)
    if [[ "$OLLAMA_HOST_CFG" == *"127.0.0.1"* ]]; then
        echo -e "  ${GREEN}✓ OLLAMA_HOST usa 127.0.0.1 (correcto)${NC}"
    elif [[ "$OLLAMA_HOST_CFG" == *"localhost"* ]]; then
        echo -e "  ${YELLOW}! OLLAMA_HOST usa localhost${NC}"
        echo "     Recomendado cambiar a: OLLAMA_HOST=http://127.0.0.1:11434"
        echo "     (en Windows, localhost puede resolver a IPv6 y fallar)"
    else
        echo -e "  Host actual: ${OLLAMA_HOST_CFG}"
    fi
else
    echo -e "  ${RED}✗ backend/.env no existe${NC}"
    echo "     - Corre: cp backend/.env.example backend/.env"
fi

echo ""
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}  Diagnóstico completo${NC}"
echo -e "${BLUE}===============================================${NC}\n"
