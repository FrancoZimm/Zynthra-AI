@echo off
REM =====================================================
REM Zynthra-AI - Setup Script (Windows)
REM =====================================================

echo.
echo === Zynthra-AI - Setup ===
echo.

REM Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo [X] Python no encontrado. Instala desde https://python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%a in ('python --version') do echo [OK] Python %%a

REM Check Node
where node >nul 2>nul
if errorlevel 1 (
    echo [X] Node.js no encontrado. Instala desde https://nodejs.org
    pause
    exit /b 1
)
for /f %%a in ('node --version') do echo [OK] Node.js %%a

REM Check Yarn
where yarn >nul 2>nul
if errorlevel 1 (
    echo [!] Yarn no encontrado. Instalando...
    call npm install -g yarn
)

REM Check Ollama
where ollama >nul 2>nul
if errorlevel 1 (
    echo [X] Ollama no encontrado. Descarga desde https://ollama.com/download
    pause
    exit /b 1
)

REM Download models
echo.
echo Descargando modelos (puede tomar varios minutos)...
call ollama pull llama3.2:1b
call ollama pull nomic-embed-text
echo [OK] Modelos descargados

REM Setup backend
echo.
echo Configurando backend...
cd backend
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip -q
pip install -q -r requirements.txt
if not exist .env copy .env.example .env
cd ..
echo [OK] Backend listo

REM Setup frontend
echo.
echo Configurando frontend...
cd frontend
call yarn install --silent
if not exist .env copy .env.example .env
cd ..
echo [OK] Frontend listo

echo.
echo === Setup completo ===
echo.
echo Para iniciar:
echo   1. MongoDB en localhost:27017
echo   2. En una terminal: ollama serve
echo   3. En otra: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn server:app --reload --port 8001
echo   4. En otra: cd frontend ^&^& yarn start
echo.
echo Abre http://localhost:3000 en tu navegador.
pause
