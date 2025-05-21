# comparador_telematico_enhanced.py

import streamlit as st
import pandas as pd
import re
import io
import os

# --- Funções Aprimoradas para Normalização ---

def normalizar_telefone(numero, strict=False):
    """
    Normaliza números de telefone com diferentes níveis de rigor.
    
    Args:
        numero: O número a ser normalizado
        strict: Se True, aplica regras estritas; se False, é mais permissivo
        
    Returns:
        Tupla (numero_normalizado, confianca) onde confianca é 'alta', 'média' ou 'baixa'
    """
    if pd.isna(numero): return None, None

    numero_str = str(numero).strip()
    numero_limpo = re.sub(r"[^\d]", "", numero_str)

    if not numero_limpo or len(numero_limpo) < 8:
        return None, None

    # Prefixos de centrais a ignorar
    # Nenhum prefixo está sendo atualmente excluído, regra mantida apenas por compatibilidade estrutural
    prefixos_invalidos = ["00000000000000000000000000"]
    if any(numero_limpo.startswith(p) for p in prefixos_invalidos):
        return None, None

    # Alta confiança: número com prefixo internacional completo
    if numero_limpo.startswith("55") and len(numero_limpo) in [12, 13]:
        return "+" + numero_limpo, "alta"

    # Alta confiança: número com 0 inicial (ex: 081991234567)
    if numero_limpo.startswith("0") and len(numero_limpo) >= 11:
        return "+55" + numero_limpo[1:], "alta"

    # Alta confiança: número com DDD local (ex: 81991234567)
    if 10 <= len(numero_limpo) <= 11:
        return "+55" + numero_limpo, "alta"

    # Média confiança: número nacional curto, mas ainda válido
    elif 8 <= len(numero_limpo) < 10:
        return "+55" + numero_limpo, "média"

    # Baixa confiança: formato incompleto, mas pode conter algo relevante
    elif 8 <= len(numero_limpo) <= 15 and not strict:
        return numero_limpo, "baixa"

    return None, None


def normalizar_imei(imei, strict=False):
    """
    Normaliza IMEIs com diferentes níveis de rigor.
    
    Args:
        imei: O IMEI a ser normalizado
        strict: Se True, aplica regras estritas; se False, é mais permissivo
        
    Returns:
        Tupla (imei_normalizado, confianca) onde confianca é 'alta', 'média' ou 'baixa'
    """
    if pd.isna(imei): return None, None
    
    imei_str = str(imei).strip()
    imei_limpo = re.sub(r'\D', '', imei_str)
    
    if not imei_limpo:
        return None, None
    
    # Alta confiança: IMEI padrão de 15 dígitos
    if len(imei_limpo) == 15:
        return imei_limpo, "alta"
    
    # Média confiança: próximo do padrão IMEI
    elif 14 <= len(imei_limpo) <= 16:
        return imei_limpo[:15], "média"
    
    # Baixa confiança: potencialmente um IMEI, mas formato não padrão
    elif len(imei_limpo) >= 8 and not strict:
        # Casos como datas (convertidas em números) ainda podem ser relevantes
        return imei_limpo, "baixa"
    
    return None, None


def normalizar_email(email, strict=False):
    """
    Normaliza endereços de e-mail com diferentes níveis de rigor.
    """
    if pd.isna(email): return None, None
    
    email_str = str(email).strip().lower()
    
    if not email_str:
        return None, None
    
    # Alta confiança: formato de e-mail padrão
    if '@' in email_str and '.' in email_str.split('@', 1)[1]:
        local, domain = email_str.split('@', 1)
        local = local.split('+')[0]  # Remove parte após + (comum em e-mails Gmail)
        return f"{local}@{domain}", "alta"
    
    # Média confiança: contém @ mas formato não totalmente padrão
    elif '@' in email_str:
        return email_str, "média"
    
    # Baixa confiança: potencialmente um e-mail, mas formato incomum
    elif not strict and ('.' in email_str or len(email_str) >= 5):
        return email_str, "baixa"
    
    return None, None


def normalizar_hash(h, strict=False):
    """
    Normaliza hashes com diferentes níveis de rigor.
    """
    if pd.isna(h): return None, None
    
    h_str = str(h).strip().lower()
    
    if not h_str:
        return None, None
    
    # Alta confiança: formato de hash hexadecimal padrão
    if re.fullmatch(r'[0-9a-f]{32,128}', h_str):
        return h_str, "alta"
    
    # Média confiança: aparenta ser hash mas não segue padrão exato
    elif re.fullmatch(r'[0-9a-f]{16,}', h_str):
        return h_str, "média"
    
    # Baixa confiança: potencialmente um hash ou identificador
    elif not strict and re.search(r'[0-9a-f]{8,}', h_str):
        return h_str, "baixa"
    
    return None, None


def normalizar_id_localizacao(id_str, strict=False):
    """
    Normaliza IDs de localização com diferentes níveis de rigor.
    """
    if pd.isna(id_str): return None, None
    
    id_clean = str(id_str).strip().upper()
    
    if not id_clean:
        return None, None
    
    # Alta confiança: ID formatado normalmente
    if len(id_clean) >= 4:
        return id_clean, "alta"
    
    # Média/Baixa confiança: potencialmente um ID, mas curto
    elif not strict and len(id_clean) > 0:
        return id_clean, "baixa"
    
    return None, None

# --- Mapeamentos de Colunas ---

COLUNA_MAP_HEURISTICO = {
    "Extratos de ERBs": {
        "telefone": ["telefone", "fone", "numero", "tel", "terminal", "msisdn", "número", "celular"],
        "imei": ["imei", "terminal id", "terminal_id", "id", "equipamento", "aparelho"]
    },
    "Dados de Contas Online (Google Location)": {
        "id_localizacao": ["location id", "obfuscated id", "id", "identifier", "locid"],
        "email": ["email", "conta google", "gmail", "conta", "e-mail", "endereco", "endereço"],
        "hash": ["hash", "md5", "sha1", "sha256", "sha512", "checksum", "digest"]
    }
}

COMPLEMENTAR_MAP_HEURISTICO = {
    "nome": ["nome", "titular", "assinante", "usuário", "usuario", "cliente", "person", "name"],
    "cpf": ["cpf", "cnpj", "documento", "doc", "documentos", "identification", "id"],
    "email_contato": ["email_contato", "contato", "contact", "alt_email", "email alternativo"],
    "data_hora": ["data", "hora", "timestamp", "time", "date", "datetime", "datahora"],
    "localizacao": ["endereco", "bairro", "cidade", "uf", "erb", "siteid", "location", "endereço", "localidade", "local", "address"]
}

# --- Configuração da Página ---

st.set_page_config("Comparador Investigativo de Dados Telemáticos", layout="wide")

st.markdown("""
<style>
footer, .reportview-container .main footer {visibility: hidden;}
.stButton>button {
    width: 100%; background-color: #0E1117; color: white; border: 1px solid #4F8BF9;
}
.stButton>button:hover {
    background-color: #4F8BF9; color: black;
}
.footer {position: fixed; bottom: 0; width: 100%; background: #0E1117; color: white; text-align: center; font-size: 12px;}
.alta-confianca {color: green; font-weight: bold;}
.media-confianca {color: orange;}
.baixa-confianca {color: red; font-style: italic;}
.stTabs [data-baseweb="tab-list"] {gap: 2px;}
.stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #0E1117; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px;}
.stTabs [aria-selected="true"] {background-color: #4F8BF9;}
.download-btn {
    background-color: #4CAF50;
    color: white;
    padding: 10px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin: 10px 0;
    width: 100%;
}
.download-btn:hover {
    background-color: #45a049;
}
</style>
<div class="footer">Desenvolvido por VINÍCIUS RIBEIRO @ CIIDS | <a href="mailto:viniciusrm18@gmail.com">viniciusrm18@gmail.com</a></div>
""", unsafe_allow_html=True)

st.title("Comparador Investigativo de Dados Telemáticos")
with st.expander("Clique para Ajuda e Objetivo da Ferramenta"):
    st.write("""
        Esta ferramenta identifica padrões entre dados telemáticos oriundos de diferentes fontes (planilhas).
        Ideal para cruzamento de telefones, IMEIs, e-mails, IDs de localização, hashes etc.

        **Passos:**
        1. Escolha o tipo de análise (ERBs ou Contas Google).
        2. Envie os arquivos separados por blocos (ex: Local A, Local B).
        3. Selecione os dados complementares.
        4. Clique em "Processar Dados e Cruzar".
    
        Obs: Cada Bloco de análise é referente a uma ERB ou antena, por isso é necessário colocar as planilhas de cada antena em blocos separados para o sistema realizar o cruzamento de dados entre os blocos.
        
        **Níveis de Confiança nos Dados:**
        - **Alta (Verde)**: Dados em formato padrão completo
        - **Média (Laranja)**: Dados em formato próximo ao padrão
        - **Baixa (Vermelho)**: Dados potencialmente relevantes, mas em formato não padrão
    """)

# --- Tipo de Análise ---

st.header("Configurar Análise")
analysis_type = st.selectbox("Tipo de Análise:", ["-- Selecione --", "Extratos de ERBs", "Dados de Contas Online (Google Location)"])
ANALYSIS_TYPE_MAPPING = {
    "Extratos de ERBs": ["telefone", "imei"],
    "Dados de Contas Online (Google Location)": ["id_localizacao", "email", "hash"]
}
data_types_to_process = ANALYSIS_TYPE_MAPPING.get(analysis_type, [])

if analysis_type != "-- Selecione --":
    st.info(f"Tipos a cruzar: {', '.join([t.upper() for t in data_types_to_process])}")

# --- Removendo Filtros de Usuário para Nível de Confiança e Rigor ---
# Definindo valores padrão
strict_mode = False  # Modo permissivo por padrão
niveis_confianca = ["baixa", "média", "alta"]  # Incluir todos os níveis de confiança

# --- Upload por Bloco ---

if 'file_blocks' not in st.session_state:
    st.session_state.file_blocks = {}
if 'block_count' not in st.session_state:
    st.session_state.block_count = 0

if st.button("Adicionar Bloco de Arquivos"):
    st.session_state.block_count += 1
    st.session_state.file_blocks[f"Bloco {st.session_state.block_count}"] = {}

for i in range(1, st.session_state.block_count + 1):
    block_id = f"Bloco {i}"
    files = st.file_uploader(f"Arquivos para {block_id}", type=["csv", "xlsx"], accept_multiple_files=True, key=f"uploader_{i}")
    if files:
        st.session_state.file_blocks[block_id] = {f.name: f for f in files}

# --- Detectar Cabeçalho ---

def detectar_cabecalho(file, filename, max_linhas=15):
    try:
        file.seek(0)
        for i in range(max_linhas):
            file.seek(0)
            if filename.endswith(".csv"):
                df = pd.read_csv(file, header=i, nrows=5, encoding="utf-8", sep=None, engine='python')
            else:
                df = pd.read_excel(file, header=i, nrows=5)
            if df.shape[1] >= 2 and sum("Unnamed" in str(c) for c in df.columns) < df.shape[1] // 2:
                return i
        return 0
    except Exception:
        return 0

# --- Complementares ---

# Checar se todos os blocos possuem pelo menos um arquivo
blocos_preenchidos = all(bool(arquivos) for arquivos in st.session_state.file_blocks.values())

if st.session_state.file_blocks and data_types_to_process and blocos_preenchidos:

    st.header("Dados Complementares")
    selected_complementary = st.multiselect(
        "Selecione os campos complementares (opcional):",
        list(COMPLEMENTAR_MAP_HEURISTICO.keys()), default=[]
    )

    if st.button("Processar Dados e Cruzar"):
        st.subheader("Status:")
        status_area = st.empty()
        progress = st.progress(0.0)
        dataframes_por_bloco, erros, registros = [], [], []
        contador = 0
        total_arquivos = sum(len(bloco) for bloco in st.session_state.file_blocks.values())

        for bloco_id, arquivos in st.session_state.file_blocks.items():
            for nome_arquivo, file in arquivos.items():
                contador += 1
                status_area.text(f"Lendo: {nome_arquivo} ({bloco_id})")
                try:
                    header_row = detectar_cabecalho(file, nome_arquivo)
                    file.seek(0)
                    if nome_arquivo.endswith(".csv"):
                        df = pd.read_csv(file, header=header_row, dtype=str, encoding='utf-8', sep=None, engine='python')
                    else:
                        df = pd.read_excel(file, header=header_row, dtype=str)
                    df = df.astype(str).replace("nan", "")
                    df.columns = [str(col).strip().lower() for col in df.columns]
                    dataframes_por_bloco.append({"df": df, "bloco": bloco_id, "nome": nome_arquivo})
                except Exception as e:
                    erros.append(f"{nome_arquivo} ({bloco_id}) -> Erro: {e}")
                progress.progress(contador / total_arquivos * 0.3)

        if len(dataframes_por_bloco) < 2:
            st.error("Necessário ao menos dois blocos com arquivos válidos.")
        else:
            normalizadores = {
                "telefone": lambda x: normalizar_telefone(x, strict_mode),
                "imei": lambda x: normalizar_imei(x, strict_mode),
                "email": lambda x: normalizar_email(x, strict_mode),
                "hash": lambda x: normalizar_hash(x, strict_mode),
                "id_localizacao": lambda x: normalizar_id_localizacao(x, strict_mode)
            }
            map_primario = COLUNA_MAP_HEURISTICO[analysis_type]
            map_complementar = COMPLEMENTAR_MAP_HEURISTICO

            # Armazenar todos os dados extraídos com seus níveis de confiança
            todos_registros = []

            for bloco in dataframes_por_bloco:
                df, bloco_id, nome_arquivo = bloco["df"], bloco["bloco"], bloco["nome"]
                
                # Primeiro, vamos identificar as colunas para cada tipo de dado
                colunas_por_tipo = {}
                for tipo in data_types_to_process:
                    colunas_tipo = [col for col in df.columns if any(k in col.lower() for k in map_primario[tipo])]
                    colunas_por_tipo[tipo] = colunas_tipo
                
                # Agora processamos cada linha
                for _, row in df.iterrows():
                    # Para cada tipo de dado, tentamos extrair de todas as colunas relevantes
                    for tipo in data_types_to_process:
                        for col in colunas_por_tipo[tipo]:
                            valor_normalizado, confianca = normalizadores[tipo](row[col])
                            
                            if valor_normalizado:
                                dado = {
                                    "valor": valor_normalizado,
                                    "tipo": tipo,
                                    "confianca": confianca,
                                    "bloco": bloco_id,
                                    "arquivo": nome_arquivo,
                                    "valor_original": row[col]
                                }
                                
                                # Adicionar dados complementares
                                for comp in selected_complementary:
                                    for comp_col in df.columns:
                                        if any(k in comp_col.lower() for k in map_complementar[comp]):
                                            dado[comp] = row[comp_col]
                                            break
                                
                                todos_registros.append(dado)

            progress.progress(0.6)
            
            # Converter para DataFrame para facilitar o processamento
            df_todos = pd.DataFrame(todos_registros)
            
            if df_todos.empty:
                st.warning("Nenhum dado relevante encontrado nos arquivos.")
            else:
                # Filtrar por nível de confiança (usando todos os níveis por padrão)
                df_filtrado = df_todos[df_todos["confianca"].isin(niveis_confianca)]
                
                # Identificar cruzamentos entre blocos
                cruzamentos = []
                for valor, grupo in df_filtrado.groupby(["valor", "tipo"]):
                    blocos_unicos = grupo["bloco"].unique()
                    if len(blocos_unicos) > 1:  # Existe em mais de um bloco
                        cruzamento = {
                            "valor": valor[0],
                            "tipo": valor[1],
                            "confianca": grupo["confianca"].iloc[0],
                            "blocos": list(blocos_unicos),
                            "ocorrencias": len(grupo)
                        }
                        
                        # Adicionar dados complementares
                        for comp in selected_complementary:
                            if comp in grupo.columns:
                                valores_comp = grupo[comp].dropna().unique()
                                cruzamento[comp] = list(valores_comp) if len(valores_comp) > 0 else []
                        
                        cruzamentos.append(cruzamento)
                
                df_cruzado = pd.DataFrame(cruzamentos)
                
                # Mostrar resultados
                if df_cruzado.empty:
                    st.warning("Nenhum cruzamento encontrado com os critérios selecionados.")
                else:
                    st.success(f"Foram encontrados {len(df_cruzado)} elementos cruzados entre blocos.")
                    
                    # Função para formatação de confiança
                    def format_confidence(df):
                        # Verificar o tamanho do DataFrame para evitar problemas com o Styler
                        total_cells = df.shape[0] * df.shape[1]
                        MAX_CELLS_STYLER = 250000  # Limite seguro para o Styler
                        
                        if total_cells > MAX_CELLS_STYLER:
                            st.warning(f"O DataFrame tem {total_cells} células, excedendo o limite para estilização. Exibindo sem cores.")
                            return df
                        else:
                            return df.style.apply(
                                lambda x: [
                                    'background-color: rgba(0, 255, 0, 0.1)' if v == 'alta' else 
                                    'background-color: rgba(255, 165, 0, 0.1)' if v == 'média' else 
                                    'background-color: rgba(255, 0, 0, 0.1)' if v == 'baixa' else 
                                    '' for v in x
                                ], 
                                subset=['confianca']
                            )
                    
                    # Exibir apenas os cruzamentos na interface, não exibindo todos os dados
                    st.subheader("Cruzamentos Identificados")
                    st.dataframe(format_confidence(df_cruzado))
                    
                    # Criar botões de download separados
                    st.subheader("Downloads Disponíveis")
                    
                    # 1. Download da planilha com os cruzamentos
                    output_cruzamentos = io.BytesIO()
                    with pd.ExcelWriter(output_cruzamentos, engine='xlsxwriter') as writer:
                        df_cruzado.to_excel(writer, index=False, sheet_name="Cruzamentos")
                        
                        # Configuração para destacar níveis de confiança na planilha
                        workbook = writer.book
                        worksheet = writer.sheets["Cruzamentos"]
                        
                        # Formatos para diferentes níveis de confiança
                        formato_alta = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                        formato_media = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
                        formato_baixa = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                        
                        # Encontrar o índice da coluna 'confianca'
                        conf_idx = df_cruzado.columns.get_loc("confianca")
                        
                        # Aplicar formatação condicional
                        worksheet.conditional_format(1, conf_idx, len(df_cruzado) + 1, conf_idx, {
                            'type': 'cell',
                            'criteria': 'equal to',
                            'value': '"alta"',
                            'format': formato_alta
                        })
                        
                        worksheet.conditional_format(1, conf_idx, len(df_cruzado) + 1, conf_idx, {
                            'type': 'cell',
                            'criteria': 'equal to',
                            'value': '"média"',
                            'format': formato_media
                        })
                        
                        worksheet.conditional_format(1, conf_idx, len(df_cruzado) + 1, conf_idx, {
                            'type': 'cell',
                            'criteria': 'equal to',
                            'value': '"baixa"',
                            'format': formato_baixa
                        })
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            "📊 Baixar Planilha de Cruzamentos (XLSX)",
                            data=output_cruzamentos.getvalue(),
                            file_name="cruzamentos_telematicos.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    # 2. Download de todos os registros extraídos
                    output_todos = io.BytesIO()
                    with pd.ExcelWriter(output_todos, engine='xlsxwriter') as writer:
                        df_todos.to_excel(writer, index=False, sheet_name="Todos os Registros")
                        
                        # Configuração similar para a planilha de todos os registros
                        workbook = writer.book
                        worksheet = writer.sheets["Todos os Registros"]
                        
                        # Formatos para diferentes níveis de confiança
                        formato_alta = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                        formato_media = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
                        formato_baixa = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                        
                        # Encontrar o índice da coluna 'confianca'
                        conf_idx = df_todos.columns.get_loc("confianca")
                        
                        # Aplicar formatação condicional
                        worksheet.conditional_format(1, conf_idx, len(df_todos) + 1, conf_idx, {
                            'type': 'cell',
                            'criteria': 'equal to',
                            'value': '"alta"',
                            'format': formato_alta
                        })
                        
                        worksheet.conditional_format(1, conf_idx, len(df_todos) + 1, conf_idx, {
                            'type': 'cell',
                            'criteria': 'equal to',
                            'value': '"média"',
                            'format': formato_media
                        })
                        
                        worksheet.conditional_format(1, conf_idx, len(df_todos) + 1, conf_idx, {
                            'type': 'cell',
                            'criteria': 'equal to',
                            'value': '"baixa"',
                            'format': formato_baixa
                        })
                    
                    with col2:
                        st.download_button(
                            "📄 Baixar Todos os Registros Extraídos (XLSX)",
                            data=output_todos.getvalue(),
                            file_name="todos_registros_extraidos.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    # Informação para o usuário sobre o que foi feito
                    st.info("""
                    **Análise concluída!**
                    
                    - Os **cruzamentos identificados** são exibidos na tabela acima
                    - Use o botão de download para obter a planilha completa com os cruzamentos destacados por nível de confiança
                    - Use o botão "Baixar Todos os Registros Extraídos" para ter acesso a todos os dados extraídos das planilhas
                    """)

            progress.progress(1.0)

            if erros:
                with st.expander("⚠️ Arquivos com Erro de Leitura"):
                    for err in erros:
                        st.error(err)

elif analysis_type == "-- Selecione --":
    st.warning("Selecione o tipo de análise para começar.")