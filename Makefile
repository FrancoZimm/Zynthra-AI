# =====================================================
# Zynthra-AI - Makefile
# =====================================================
# Uso:
#   make install     - Instalar todas las dependencias
#   make start       - Arrancar todos los servicios
#   make stop        - Detener todos los servicios
#   make backend     - Solo el backend
#   make frontend    - Solo el frontend
#   make ollama      - Solo Ollama
#   make logs        - Ver logs en vivo
#   make clean       - Limpiar archivos temporales
#   make docker-up   - Arrancar todo con Docker
#   make docker-down - Detener Docker
# =====================================================

.PHONY: help install start stop backend frontend ollama mongo logs clean docker-up docker-down test

help:
	@echo "Zynthra-AI - Comandos disponibles:"
	@echo ""
	@echo "  make install      Instalar todas las dependencias"
	@echo "  make start        Arrancar backend + frontend + ollama"
	@echo "  make stop         Detener todos los servicios"
	@echo "  make backend      Solo backend (FastAPI)"
	@echo "  make frontend     Solo frontend (React)"
	@echo "  make ollama       Solo Ollama"
	@echo "  make logs         Ver logs en vivo"
	@echo "  make test         Correr tests"
	@echo "  make clean        Limpiar archivos temporales"
	@echo "  make docker-up    Arrancar todo con Docker Compose"
	@echo "  make docker-down  Detener Docker Compose"

install:
	@echo "Instalando dependencias..."
	@bash setup.sh

start:
	@bash start.sh

stop:
	@pkill -f "uvicorn server:app" || true
	@pkill -f "react-scripts start" || true
	@pkill -x "ollama" || true
	@echo "✓ Servicios detenidos"

backend:
	@cd backend && . venv/bin/activate && uvicorn server:app --reload --port 8001

frontend:
	@cd frontend && yarn start

ollama:
	@ollama serve

mongo:
	@mkdir -p data/db
	@mongod --dbpath ./data/db

logs:
	@tail -f logs/backend.log logs/frontend.log logs/ollama.log

test:
	@cd backend && . venv/bin/activate && pytest -v

clean:
	@rm -rf logs/*.log
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Limpieza completa"

docker-up:
	@docker-compose up -d
	@echo "✓ Servicios Docker corriendo. Abre http://localhost:3000"

docker-down:
	@docker-compose down
	@echo "✓ Servicios Docker detenidos"
