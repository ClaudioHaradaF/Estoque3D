@echo off
title Estoque3D - Controle de Estoque
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

cls
echo ========================================
echo         ESTOQUE 3D
echo    Controle de Estoque e Vendas
echo ========================================
echo.
echo Instalando dependencias...
pip install -q -r requirements.txt 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao instalar dependencias.
    echo Tente executar como Administrador.
)
echo.
echo Iniciando servidor...
echo.
echo   Acesse: http://localhost:5000
echo.
echo   Para parar: feche esta janela ou pressione Ctrl+C
echo ========================================
echo.

start "" http://localhost:5000
python run.py

echo.
echo Servidor encerrado.
pause
