@echo off
REM =====================================================
REM Zynthra-AI - Script de Diagnóstico (Windows)
REM =====================================================
REM Verifica que cada componente funcione correctamente

echo.
echo ===============================================
echo   Zynthra-AI - Diagnostico del sistema
echo ===============================================
echo.

echo [1/5] Verificando Ollama en 127.0.0.1:11434...
curl -s http://127.0.0.1:11434/api/tags >nul 2>nul
if errorlevel 1 (
    echo   [X] Ollama NO responde en 127.0.0.1:11434
    echo       - Verifica que 'ollama serve' este corriendo
    echo       - Prueba: ollama list
) else (
    echo   [OK] Ollama responde correctamente
    curl -s http://127.0.0.1:11434/api/tags
    echo.
)

echo.
echo [2/5] Verificando Ollama via localhost:11434...
curl -s --connect-timeout 3 http://localhost:11434/api/tags >nul 2>nul
if errorlevel 1 (
    echo   [!] localhost:11434 NO responde ^(posible problema IPv6^)
    echo       - Usa 127.0.0.1 en lugar de localhost en .env
) else (
    echo   [OK] localhost:11434 tambien funciona
)

echo.
echo [3/5] Verificando Backend FastAPI en puerto 8001...
curl -s http://127.0.0.1:8001/api/health >nul 2>nul
if errorlevel 1 (
    echo   [X] Backend NO responde en puerto 8001
    echo       - El backend no esta corriendo
    echo       - Corre: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn server:app --reload --port 8001
) else (
    echo   [OK] Backend FastAPI responde
    echo.
    echo   Respuesta /api/health:
    curl -s http://127.0.0.1:8001/api/health
    echo.
)

echo.
echo [4/5] Verificando Frontend en puerto 3000...
curl -s --connect-timeout 3 http://127.0.0.1:3000 >nul 2>nul
if errorlevel 1 (
    echo   [X] Frontend NO responde en puerto 3000
    echo       - Corre: cd frontend ^&^& yarn start
) else (
    echo   [OK] Frontend React responde
)

echo.
echo [5/5] Verificando MongoDB en puerto 27017...
netstat -an | findstr :27017 | findstr LISTENING >nul
if errorlevel 1 (
    echo   [!] MongoDB NO parece estar corriendo en puerto 27017
    echo       - Si lo necesitas: mongod --dbpath ./data/db
) else (
    echo   [OK] MongoDB escucha en puerto 27017
)

echo.
echo ===============================================
echo   Diagnostico completo
echo ===============================================
echo.
echo Si alguno da [X]:
echo   1. Asegurate de tener todos los servicios iniciados
echo   2. Corre start.bat para levantar todo
echo   3. Si Ollama da problemas, verifica backend\.env:
echo      OLLAMA_HOST=http://127.0.0.1:11434
echo.
pause
