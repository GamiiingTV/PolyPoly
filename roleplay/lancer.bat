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

rem --- Moteur gratuit (IA locale) : il faut Ollama -------------------------
findstr /r /c:"^moteur *= *\"local\"" config.toml >nul
if not errorlevel 1 (
    where ollama >nul 2>nul
    if errorlevel 1 if not exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        echo Installation d Ollama, l IA gratuite qui tourne sur ton PC...
        winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
        if errorlevel 1 (
            echo Installe Ollama a la main depuis https://ollama.com/download puis relance.
            start https://ollama.com/download
            pause
            exit /b 1
        )
    )
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe" start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
)

rem --- Moteur payant (Claude) : il faut la cle API -------------------------
findstr /r /c:"^moteur *= *\"claude\"" config.toml >nul
if not errorlevel 1 if not exist ".env" (
    echo Il manque le fichier .env avec ta cle API Anthropic. Voir README.md.
    copy ".env.exemple" ".env" >nul
    notepad ".env"
)

".venv\Scripts\python.exe" -m souffleur %*
if errorlevel 1 pause
