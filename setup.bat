@echo off
title Estoque3D - Setup
cd /d %~dp0

echo ========================================
echo  Estoque3D - Configuracao
echo ========================================
echo.

REM 1. Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale Python 3.12+ e tente novamente.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set pyver=%%v
echo [OK] Python %pyver% encontrado

REM 2. Verificar Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Git nao encontrado. Instale Git e tente novamente.
    pause
    exit /b 1
)
echo [OK] Git encontrado

REM 3. Clonar se necessario
if not exist ".git" (
    if exist "Estoque3D" (
        cd Estoque3D
    ) else (
        echo.
        echo Clonando repositorio...
        git clone https://github.com/ClaudioHaradaF/Estoque3D.git
        cd Estoque3D
    )
)
echo [OK] Repositorio pronto em %cd%

REM 4. Criar ambiente virtual
if not exist ".venv" (
    echo.
    echo Criando ambiente virtual...
    python -m venv .venv
)
echo [OK] Ambiente virtual pronto

REM 5. Ativar e instalar dependencias
echo.
echo Instalando dependencias...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo [OK] Dependencias instaladas

REM 6. Criar pastas necessarias
if not exist "instance" mkdir instance
if not exist "app\static\uploads" mkdir app\static\uploads
if not exist "app\config" mkdir app\config

REM 7. Lembretes
cls
echo.
echo ========================================
echo  ARQUIVOS PARA COPIAR DO PC ANTIGO
echo ========================================
echo.
echo  Copie ESTES 3 itens do computador antigo:
echo.
echo  1. D:\Trash\Estoque3D\instance\estoque3d.db
echo     ^> para  %cd%\instance\
echo.
echo  2. D:\Trash\Estoque3D\app\static\uploads\
echo     ^> para  %cd%\app\static\uploads\
echo.
echo  3. D:\Trash\Estoque3D\app\config\google-creds.json
echo     ^> para  %cd%\app\config\
echo.
echo ========================================
echo.
echo  Cole os arquivos nas pastas indicadas
echo  e pressione qualquer tecla para continuar...
pause >nul

REM 8. Aplicar migrations
echo.
echo Aplicando migrations no banco de dados...
call .venv\Scripts\activate.bat
flask db upgrade
echo [OK] Banco de dados pronto

REM 9. Iniciar servidor
echo.
echo ========================================
echo  Servidor iniciando em:
echo  http://localhost:5000
echo ========================================
echo.
echo  Pressione Ctrl+C no terminal para parar.
echo.
python run.py

pause
