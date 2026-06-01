@echo off
title Estoque3D - Modo Rede
cd /d "%~dp0"

cls
echo ========================================
echo         ESTOQUE 3D - MODO REDE
echo    Acessivel de outros computadores
echo ========================================
echo.
echo Instalando dependencias...
pip install -q -r requirements.txt 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao instalar dependencias.
)
echo.
ipconfig | findstr /i "IPv4" | findstr /v "127.0.0.1"
echo.
echo   Acesse de OUTRO computador na rede via:
echo   http://[IP ACIMA]:5000
echo.
echo   Ou localmente:
echo   http://localhost:5000
echo.
echo   Para parar: feche esta janela ou pressione Ctrl+C
echo ========================================
echo.

start "" http://localhost:5000
python run.py

echo.
echo Servidor encerrado.
pause
