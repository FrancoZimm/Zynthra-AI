#!/bin/bash
# =====================================================
# Zynthra-AI - Setup Script (Linux/macOS)
# =====================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Zynthra-AI - Setup ===${NC}\n"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}X Python 3 no encontrado. Instala desde https://python.org${NC}"
    exit 1
fi
echo -e "${GREEN}OK Python $(python3 --version | cut -d' ' -f2)${NC}"

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}X Node.js no encontrado. Instala desde https://nodejs.org${NC}"
    exit 1
fi
echo -e "${GREEN}OK Node.js $(node --version)${NC}"

# Check Yarn
if ! command -v yarn &> /dev/null; then
    echo -e "${YELLOW}! Yarn no encontrado. Instalando...${NC}"
    npm install -g yarn
fi
echo -e "${GREEN}OK Yarn $(yarn --version)${NC}"

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}! Ollama no encontrado. Instalando...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
fi
echo -e "${GREEN}OK Ollama instalado${NC}"

# Download models
echo -e "\n${YELLOW}Descargando modelos (puede tomar varios minutos)...${NC}"
ollama pull llama3.2:1b
ollama pull nomic-embed-text
echo -e "${GREEN}OK Modelos descargados${NC}"

# Setup backend
echo -e "\n${YELLOW}Configurando backend...${NC}"
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
[ ! -f .env ] && cp .env.example .env
cd ..
echo -e "${GREEN}OK Backend listo${NC}"

# Setup frontend
echo -e "\n${YELLOW}Configurando frontend...${NC}"
cd frontend
yarn install --silent
[ ! -f .env ] && cp .env.example .env
cd ..
echo -e "${GREEN}OK Frontend listo${NC}"

echo -e "\n${GREEN}=== Setup completo ===${NC}"
echo -e "\nPara iniciar la aplicación:"
echo -e "  ${YELLOW}1.${NC} MongoDB en localhost:27017"
echo -e "  ${YELLOW}2.${NC} Ollama: ${GREEN}ollama serve${NC}"
echo -e "  ${YELLOW}3.${NC} Backend: ${GREEN}cd backend && source venv/bin/activate && uvicorn server:app --reload --port 8001${NC}"
echo -e "  ${YELLOW}4.${NC} Frontend: ${GREEN}cd frontend && yarn start${NC}"
echo -e "\nAbre ${GREEN}http://localhost:3000${NC} en tu navegador.\n"
