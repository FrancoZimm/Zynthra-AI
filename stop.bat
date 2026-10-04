@echo off
REM Detener servicios de Zynthra-AI
echo.
echo Deteniendo servicios de Zynthra-AI...

taskkill /FI "WINDOWTITLE eq Zynthra Backend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Zynthra Frontend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Ollama*" /T /F >nul 2>nul

echo [OK] Servicios detenidos
echo.
echo Ollama puede seguir corriendo en background.
echo Para detenerlo: taskkill /IM ollama.exe /F
echo.
pause
