================================================================================
COMPARADOR INVESTIGATIVO DE DADOS TELEMÁTICOS
================================================================================

Este sistema foi desenvolvido para auxiliar na análise e cruzamento de dados
telemáticos oriundos de planilhas (por exemplo, registros de telefones, IMEIs,
e-mails, hashes, etc.), voltado para apoiar investigações e análises técnicas.

--------------------------------------------------------------------------------
ESTRUTURA DA PASTA
--------------------------------------------------------------------------------
A pasta distribuída (arquivo ZIP) contém os seguintes itens:

1. **app.py**  
   - Arquivo principal contendo o código do sistema.

2. **iniciar.bat**  
   - Script para iniciar o sistema automaticamente. Ele fará as seguintes etapas:
     - Verificar se o Python está instalado.
     - Criar um ambiente virtual local (caso não exista).
     - Instalar as dependências necessárias (Streamlit, pandas, openpyxl, xlsxwriter).
     - Executar o aplicativo com o comando `streamlit run app.py`.

3. **streamlit/**  
   - Pasta contendo configurações para o Streamlit, com o tema dark personalizado.
   - O arquivo principal de configuração é `config.toml`, onde o tema dark foi definido.

4. **README.txt**  
   - Este arquivo, com todas as instruções para uso e distribuição.

--------------------------------------------------------------------------------
INSTRUÇÕES DE USO
--------------------------------------------------------------------------------
1. **Extraia o arquivo ZIP** para uma pasta local.
2. Certifique-se de que o Python está instalado no seu sistema e que durante a
   instalação a opção "Add Python to PATH" foi marcada. Se não estiver instalado,
   baixe e instale o Python em modo "usuário" em:
       https://www.python.org/downloads/
3. Dentro da pasta extraída, dê um duplo clique no arquivo **iniciar.bat**.
   - O script criará um ambiente virtual local (.venv) automaticamente e instalará
     as dependências necessárias.
   - O sistema será iniciado e o Streamlit abrirá o aplicativo no seu navegador
     padrão, geralmente na URL: `http://localhost:8501`
4. Siga as instruções da interface para:
   - Selecionar o tipo de análise (ERBs ou Dados de Contas Online, etc.).
   - Adicionar os blocos de arquivos e os dados complementares se desejar.
   - Processar os dados e visualizar os cruzamentos.
   - Baixar os resultados em planilhas Excel, CSV ou JSON conforme necessário.
5. **Observação:**  
   - A primeira vez que o sistema for iniciado, ele precisará de acesso à internet
     para baixar as dependências e (se necessário) instalar o Python.  
   - Depois da primeira execução, o ambiente virtual (.venv) estará criado e
     as dependências já instaladas, permitindo execuções subsequentes sem a necessidade
     de conexão à internet.

--------------------------------------------------------------------------------
SUPORTE E CONTATO
--------------------------------------------------------------------------------
Desenvolvido por: VINÍCIUS RIBEIRO  
Instituição: ESINT | CIIDS  
E-mail: viniciusrm18@gmail.com

Caso encontre problemas ou tenha sugestões, entre em contato através do e-mail.

================================================================================
