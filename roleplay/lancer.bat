@echo off
rem ============================================================
rem  Le Souffleur - lanceur Windows
rem  Double-clic : installe tout la premiere fois, puis lance.
rem  Options : lancer.bat --simulation   /   lancer.bat --peripheriques
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Premiere installation, patience...
    py -3 -m venv .venv || python -m venv .venv
    if errorlevel 1 (
        echo Python est introuvable. Installe Python 3.12 depuis python.org en cochant "Add to PATH".
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo L installation a echoue. Lis le message ci-dessus.
        pause
        exit /b 1
    )
)

if not exist ".env" (
    echo Il manque le fichier .env avec ta cle API Anthropic. Voir README.md.
    copy ".env.exemple" ".env" >nul
    notepad ".env"
)

".venv\Scripts\python.exe" -m souffleur %*
if errorlevel 1 pause
