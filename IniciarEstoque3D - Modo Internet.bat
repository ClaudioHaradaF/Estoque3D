@echo off
title Estoque3D - Modo Internet
cd /d "%~dp0"

:: ── Auto-elevação para Admin ──
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   Solicitando privilegios de Administrador...
    echo.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Mata processos ngork residuais
taskkill /F /IM ngrok.exe >nul 2>&1

cls
echo ========================================
echo     ESTOQUE 3D - MODO INTERNET
echo    Acesso de qualquer lugar
echo ========================================
echo.
echo Instalando dependencias...
pip install -q -r requirements.txt 2>nul
pip install -q pyngrok 2>nul
echo.
echo Iniciando servidor + tunel ngrok...
echo.
echo   Aguarde alguns segundos ate que a URL
echo   publica seja exibida na tela.
echo ========================================
echo.

python run_remoto.py

echo.
echo Servidor encerrado.
pause
