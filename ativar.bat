@echo off
REM Ativa o ambiente virtual no Prompt de Comando (cmd.exe) ou no PowerShell.
REM Uso:  ativar.bat        -> ativa nesta janela
REM       ativar.bat cmd    -> abre um cmd ja ativado
if /i "%~1"=="cmd" (
    cmd /k "%~dp0.venv\Scripts\activate.bat"
    exit /b
)
if not exist "%~dp0.venv\Scripts\activate.bat" (
    echo Ambiente .venv nao encontrado. Rode antes:  python -m venv .venv
    exit /b 1
)
call "%~dp0.venv\Scripts\activate.bat"
python --version
where python
