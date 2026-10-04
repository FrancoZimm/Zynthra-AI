@echo off
REM =====================================================
REM Zynthra-AI - FIX ALL (Windows)
REM =====================================================
REM Arregla automaticamente configuraciones problematicas

echo.
echo ===============================================
echo   Zynthra-AI - Reparando configuracion
echo ===============================================
echo.

REM === 1. Detener servicios corriendo ===
echo [1/5] Deteniendo servicios...
taskkill /FI "WINDOWTITLE eq Zynthra Backend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Zynthra Frontend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Ollama*" /T /F >nul 2>nul
echo   [OK] Servicios detenidos

REM === 2. Arreglar frontend/.env ===
echo [2/5] Arreglando frontend\.env...
(
  echo REACT_APP_BACKEND_URL=http://localhost:8001
  echo WDS_SOCKET_PORT=3000
  echo BROWSER=none
) > frontend\.env
echo   [OK] frontend\.env configurado para localhost

REM === 3. Arreglar backend/.env ===
echo [3/5] Verificando backend\.env...
if not exist "backend\.env" (
    copy backend\.env.example backend\.env >nul
    echo   [OK] backend\.env creado desde .env.example
) else (
    powershell -Command "(Get-Content backend\.env) -replace 'localhost:11434', '127.0.0.1:11434' | Set-Content backend\.env"
    echo   [OK] backend\.env actualizado con 127.0.0.1
)

REM === 4. Limpiar cache python ===
echo [4/5] Limpiando cache Python...
if exist "backend\services\__pycache__" rmdir /s /q "backend\services\__pycache__" >nul 2>nul
if exist "backend\config\__pycache__" rmdir /s /q "backend\config\__pycache__" >nul 2>nul
if exist "backend\models\__pycache__" rmdir /s /q "backend\models\__pycache__" >nul 2>nul
if exist "backend\__pycache__" rmdir /s /q "backend\__pycache__" >nul 2>nul
echo   [OK] Cache limpio

REM === 5. Verificar dependencias ===
echo [5/5] Verificando dependencias...
if not exist "backend\venv" (
    echo   [!] venv no existe. Corre setup.bat primero.
    pause
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo   [!] node_modules no existe. Corre setup.bat primero.
    pause
    exit /b 1
)
echo   [OK] Dependencias presentes

echo.
echo ===============================================
echo   Todo reparado. Ahora corre: start.bat
echo ===============================================
echo.
pause
