COMPARADOR INVESTIGATIVO DE DADOS TELEMÁTICOS
Desenvolvido por: VINÍCIUS RIBEIRO @ CIIDS
Contato: viniciusrm18@gmail.com

DESCRIÇÃO DA FERRAMENTA

O Comparador Investigativo de Dados Telemáticos é uma ferramenta desenvolvida em Python com Streamlit, voltada para cruzamento inteligente de dados telemáticos provenientes de diversas fontes.

OBJETIVO:
Identificar rapidamente elementos comuns entre diferentes blocos de dados como:

- Números de telefone
- IMEIs
- E-mails
- IDs de localização
- Hashes

Com ênfase na normalização dos dados e na atribuição de níveis de confiança.

FUNCIONALIDADES PRINCIPAIS

- Upload de múltiplos arquivos separados por blocos lógicos (ex.: Local A, Local B)
- Normalização automática dos dados com detecção de padrões e ruídos
- Atribuição de níveis de confiança: alta, média ou baixa
- Cruzamento entre blocos, detectando elementos que se repetem em diferentes fontes
- Geração automática de relatórios em formato Excel (.xlsx), com formatação condicional para destacar níveis de confiança
- Interface intuitiva e responsiva desenvolvida com Streamlit
- Exportação de dois tipos de relatórios:
  - Somente cruzamentos identificados
  - Todos os registros extraídos

TECNOLOGIAS UTILIZADAS

- Python 3.8 ou superior
- Streamlit
- Pandas
- OpenPyXL
- XlsxWriter

COMO UTILIZAR

1. Clone o repositório:
   git clone https://github.com/Viniciusrm18/comparador_telematico.git
   cd comparador_telematico

2. Crie e ative o ambiente virtual (opcional mas recomendado):
   python -m venv venv
   source venv/bin/activate   (Linux/Mac)
   venv\Scripts\activate      (Windows)

3. Instale as dependências:
   pip install -r requirements.txt

4. Execute o aplicativo:
   streamlit run app.py

FLUXO DE USO

1. Selecione o tipo de análise:
   - Extratos de ERBs
   - Dados de Contas Online (Google Location)

2. Clique em "Adicionar Bloco de Arquivos" e faça o upload dos arquivos correspondentes ao bloco (CSV ou XLSX). 
   Repita para cada bloco desejado.

3. Após ter blocos com arquivos e o tipo de análise selecionado, a interface libera o botão:
   "Processar Dados e Cruzar"

4. Acompanhe o progresso da análise.

5. Visualize os cruzamentos identificados.

6. Faça o download dos relatórios em Excel:
   - Planilha de cruzamentos.
   - Todos os registros extraídos.

ENTRADA DE DADOS ACEITA

- Arquivos .csv ou .xlsx
- Estruturas de colunas flexíveis, com mapeamento heurístico:
  - Telefones: telefone, msisdn, numero, etc.
  - IMEI: imei, terminal id, etc.
  - E-mails: email, gmail, etc.
  - Hashes: md5, sha1, etc.
  - IDs de localização: location id, locid, etc.

Cabeçalhos são detectados automaticamente.

SAÍDA GERADA

- Arquivos .xlsx com formatação condicional:
  - Verde: Alta confiança
  - Laranja: Média confiança
  - Vermelho: Baixa confiança
- Tabela exibida na interface com destaque visual.

DEPENDÊNCIAS

streamlit
pandas
openpyxl
xlsxwriter

Instale via:
pip install -r requirements.txt

LICENÇA

Este projeto é de uso interno e investigativo. 
Direitos reservados ao autor.

AUTOR

Vinícius Ribeiro
Especialista em Inteligência Investigativa — Polícia Civil de Pernambuco
viniciusrm18@gmail.com

POSSÍVEIS EVOLUÇÕES

- Processamento assíncrono ou vetorizado
- Processamento em chunks para grandes datasets
- Integração com banco de dados
- Dashboard de análise com filtros dinâmicos
- Logs detalhados para auditoria

DÚVIDAS OU SUGESTÕES?

Entre em contato: viniciusrm18@gmail.com

STATUS DO PROJETO

Em produção
Evoluções planejadas para o projeto "Comparador Telemático Avançado"
