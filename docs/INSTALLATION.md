# Guía de instalación detallada

Esta guía cubre la instalación paso a paso en Windows, macOS y Linux.

## Requisitos mínimos

- **CPU**: 4 cores (8 recomendado)
- **RAM**: 8 GB (16 GB recomendado)
- **Disco**: 10 GB libres
- **SO**: Windows 10+, macOS 12+, Ubuntu 20.04+
- **Python**: 3.11 o superior
- **Node.js**: 18 o superior

## 1. Instalar Python

### Windows
Descargar desde [python.org](https://www.python.org/downloads/). Marcar "Add Python to PATH".

### macOS
```bash
brew install python@3.11
```

### Ubuntu / Debian
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

## 2. Instalar Node.js y Yarn

### Windows / macOS
Descargar desde [nodejs.org](https://nodejs.org/) (LTS). Luego:
```bash
npm install -g yarn
```

### Ubuntu / Debian
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs
npm install -g yarn
```

## 3. Instalar MongoDB

### Opción A: MongoDB Community (local)
- Windows: [mongodb.com/try/download](https://www.mongodb.com/try/download/community)
- macOS: `brew install mongodb-community`
- Ubuntu: ver [guía oficial](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/)

### Opción B: Docker
```bash
docker run -d -p 27017:27017 --name mongodb mongo:7
```

## 4. Instalar Ollama

### Linux / WSL
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS / Windows
Descargar instalador de [ollama.com/download](https://ollama.com/download).

### Verificar instalación
```bash
ollama --version
ollama serve   # en otra terminal si no es servicio
```

## 5. Descargar modelos

```bash
# LLM ligero recomendado (1.3 GB)
ollama pull llama3.2:1b

# Embeddings (275 MB)
ollama pull nomic-embed-text
```

Alternativas según tu hardware:
```bash
# Si tienes 16+ GB RAM, mejor calidad:
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
```

## 6. Clonar e instalar el proyecto

```bash
git clone https://github.com/tu-usuario/zynthra-ai.git
cd zynthra-ai
```

### Opción rápida: script automático

**Linux / macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### Opción manual

**Backend:**
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

**Frontend:**
```bash
cd ../frontend
yarn install
cp .env.example .env
```

## 7. Levantar todo

Abre **4 terminales**:

**Terminal 1 — MongoDB** (si no es servicio)
```bash
mongod --dbpath ./data
```

**Terminal 2 — Ollama** (si no es servicio)
```bash
ollama serve
```

**Terminal 3 — Backend**
```bash
cd backend
source venv/bin/activate   # Windows: venv\Scripts\activate
uvicorn server:app --reload --port 8001
```

**Terminal 4 — Frontend**
```bash
cd frontend
yarn start
```

Abre [http://localhost:3000](http://localhost:3000).

## 8. Configurar en Visual Studio Code

1. Abre el proyecto: `code .`
2. Extensiones recomendadas:
   - **Python** (Microsoft)
   - **Pylance**
   - **ES7+ React/Redux/React-Native snippets**
   - **Tailwind CSS IntelliSense**
   - **ESLint**
   - **Prettier**

3. Configuración recomendada (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

4. Launch configs (`.vscode/launch.json`) para debug:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["server:app", "--reload", "--port", "8001"],
      "cwd": "${workspaceFolder}/backend",
      "console": "integratedTerminal"
    }
  ]
}
```

## Verificación

1. En el sidebar, el **Estado** debe mostrar:
   - ✅ Ollama conectado
   - ⚠️ 0 chunks indexados (normal al inicio)

2. Haz click en **Texto**, pega algún contenido, dale un nombre y click en **Indexar**.

3. Haz una pregunta relacionada al contenido. El sistema debe responder citando fuentes.

## Solución de problemas

### "Ollama desconectado"
```bash
# Verificar que Ollama está corriendo
curl http://localhost:11434/api/tags
```
Si falla: `ollama serve` en otra terminal.

### "Cannot connect to MongoDB"
Verifica que MongoDB está corriendo en `localhost:27017`.

### "Model not found"
```bash
ollama list                     # ver modelos instalados
ollama pull llama3.2:1b         # reinstalar
```

### El frontend no se conecta al backend
Verifica que `frontend/.env` tenga:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Muy lento
- Usa un modelo más pequeño (`llama3.2:1b` en vez de `3b`)
- Reduce `TOP_K_RESULTS` en `.env`
- Cierra otras apps que consuman RAM
