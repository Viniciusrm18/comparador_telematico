@echo off
setlocal

:: Verifica se o Python está disponível
where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python não encontrado no sistema.
    echo Baixe e instale o Python em modo de usuário: https://www.python.org/downloads/
    pause
    exit /b
)

:: Cria ambiente virtual se não existir
if not exist ".venv" (
    echo [+] Criando ambiente virtual...
    python -m venv .venv
)

:: Ativa o ambiente virtual
call .venv\Scripts\activate.bat

:: Instala dependências diretamente (sem requirements.txt)
echo [+] Instalando bibliotecas necessárias...
pip install --upgrade pip
pip install streamlit pandas openpyxl xlsxwriter

:: Executa o sistema
echo [+] Iniciando o sistema...
streamlit run app.py

endlocal
pause
