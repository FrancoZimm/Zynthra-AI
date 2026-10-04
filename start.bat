@echo off
REM =====================================================
REM Zynthra-AI - START ALL (Windows)
REM =====================================================

echo.
echo ===============================================
echo   Zynthra-AI - Iniciando servicios
echo ===============================================
echo.

REM Verificar prerrequisitos
where ollama >nul 2>nul
if errorlevel 1 (echo [X] Ollama no instalado & pause & exit /b 1)

where python >nul 2>nul
if errorlevel 1 (echo [X] Python no instalado & pause & exit /b 1)

where yarn >nul 2>nul
if errorlevel 1 (echo [X] Yarn no instalado & pause & exit /b 1)

if not exist "backend\venv" (echo [X] Corre primero: setup.bat & pause & exit /b 1)
if not exist "frontend\node_modules" (echo [X] Corre primero: setup.bat & pause & exit /b 1)

REM === Auto-fix del frontend/.env ===
REM Reemplaza la URL del preview por localhost si aplica
if exist "frontend\.env" (
    findstr /C:"emergentagent.com" "frontend\.env" >nul 2>nul
    if not errorlevel 1 (
        echo [!] Detectado .env con URL del preview. Arreglando...
        powershell -Command "(Get-Content frontend\.env) -replace 'REACT_APP_BACKEND_URL=.*', 'REACT_APP_BACKEND_URL=http://localhost:8001' -replace 'WDS_SOCKET_PORT=.*', 'WDS_SOCKET_PORT=3000' | Set-Content frontend\.env"
        echo BROWSER=none >> frontend\.env
        echo   [OK] frontend\.env arreglado
    )
) else (
    echo [!] Creando frontend\.env...
    copy frontend\.env.example frontend\.env >nul
)

REM Verificar que backend/.env exista
if not exist "backend\.env" (
    echo [!] Creando backend\.env...
    copy backend\.env.example backend\.env >nul
)

REM === 1. Ollama ===
curl -s --connect-timeout 2 http://127.0.0.1:11434/api/tags >nul 2>nul
if errorlevel 1 (
    echo [1/3] Iniciando Ollama...
    start "Ollama" cmd /k "ollama serve"
    timeout /t 4 /nobreak >nul
) else (
    echo [1/3] Ollama ya corriendo [OK]
)

REM === 2. Backend ===
echo [2/3] Iniciando Backend...
start "Zynthra Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn server:app --reload --port 8001"
timeout /t 6 /nobreak >nul

REM === 3. Frontend (BROWSER=none para evitar duplicacion) ===
echo [3/3] Iniciando Frontend...
start "Zynthra Frontend" cmd /k "cd frontend && set BROWSER=none && yarn start"

echo.
echo Esperando a que frontend este listo...
timeout /t 12 /nobreak >nul

echo.
echo ===============================================
echo   Listo. Abriendo http://localhost:3000
echo ===============================================
start http://localhost:3000

echo.
echo Servicios corriendo en ventanas separadas:
echo   - Ollama (si no estaba)
echo   - Zynthra Backend  -^> :8001
echo   - Zynthra Frontend -^> :3000
echo.
echo Para detener: stop.bat (o cerra las ventanas)
echo.
timeout /t 3 /nobreak >nul
