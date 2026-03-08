# comparador_telematico_enhanced.py

import streamlit as st
import pandas as pd
import re
import io
import os
import time

# --- Funções Aprimoradas para Normalização ---

def _limpar_valor_excel(valor):
    """Remove sufixos de float (.0), trata notação científica e espaços de valores vindos do Excel."""
    if pd.isna(valor): return ""
    v_str = str(valor).strip()
    
    # Se parecer número (incluindo notação científica), converter para inteiro e depois string
    if re.match(r'^-?\d+(\.\d+)?([eE][-+]?\d+)?$', v_str):
        try:
            return '{:.0f}'.format(float(valor))
        except (ValueError, TypeError):
            pass
            
    if v_str.endswith('.0'): v_str = v_str[:-2]
    return v_str

def normalizar_telefone(numero, strict=False):
    """
    Normaliza números de telefone com foco no padrão brasileiro e lida com o 9º dígito.
    """
    v_limpo = _limpar_valor_excel(numero)
    if not v_limpo: return None, None

    # Remove tudo que não é dígito
    numero_limpo = re.sub(r"[^\d]", "", v_limpo)

    if not numero_limpo or len(numero_limpo) < 8:
        return None, None

    # NOVO: Filtro para números de centrais/inválidos (ex: 00000000, 11111111)
    # Se todos os dígitos forem iguais, ignora
    if len(set(numero_limpo)) == 1:
        return None, None

    # Remove prefixo 0 inicial se houver
    if numero_limpo.startswith("0") and len(numero_limpo) > 10:
        numero_limpo = numero_limpo[1:]

    # Remove prefixo 55 (Brasil) se houver
    if numero_limpo.startswith("55") and len(numero_limpo) >= 12:
        numero_limpo = numero_limpo[2:]

    # Casos de números nacionais (com DDD)
    if 10 <= len(numero_limpo) <= 11:
        # Se tem 10 dígitos, avaliar se deve adicionar o 9 (celular)
        if len(numero_limpo) == 10:
            ddd = numero_limpo[:2]
            prefixo = numero_limpo[2]
            # No Brasil, celulares começam com 6, 7, 8 ou 9
            if prefixo in ['6', '7', '8', '9']:
                numero_normalizado = "+55" + ddd + "9" + numero_limpo[2:]
                return numero_normalizado, "média"
            else:
                return "+55" + numero_limpo, "alta"
        
        # Se tem 11 dígitos, verificar se o 9 está no lugar certo
        if len(numero_limpo) == 11:
            if numero_limpo[2] == '9':
                return "+55" + numero_limpo, "alta"
            else:
                return "+55" + numero_limpo, "baixa"

    # Números curtos (sem DDD) - menos confiáveis para cruzamento
    elif 8 <= len(numero_limpo) <= 9:
        if len(numero_limpo) == 8:
            # Tentar normalizar para 9 dígitos se for celular
            if numero_limpo[0] in ['6', '7', '8', '9']:
                return "9" + numero_limpo, "baixa"
        return numero_limpo, "baixa"

    # Fallback para outros formatos (pode ser internacional)
    if len(numero_limpo) > 11 and not strict:
        return "+" + numero_limpo, "baixa"

    return None, None


def normalizar_imei(imei, strict=False):
    """
    Normaliza IMEIs lidando com conversões de float do Excel.
    """
    v_limpo = _limpar_valor_excel(imei)
    if not v_limpo: return None, None
    
    imei_limpo = re.sub(r'\D', '', v_limpo)
    
    if not imei_limpo:
        return None, None
    
    # Alta confiança: IMEI padrão de 15 dígitos
    if len(imei_limpo) == 15:
        return imei_limpo, "alta"
    
    # Média confiança: próximo do padrão IMEI (14 ou 16 dígitos)
    elif 14 <= len(imei_limpo) <= 16:
        return imei_limpo[:15], "média"
    
    # Baixa confiança: potencialmente um IMEI, mas formato não padrão
    elif len(imei_limpo) >= 8 and not strict:
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
        "telefone": [
            "telefone", "fone", "numero", "tel", "terminal", "msisdn", "número", "celular", 
            "calling", "called", "origem", "destino", "caller", "callee", "dialed", "chamador", "chamado",
            "a_party", "b_party", "address", "orig", "dest", "v_msisdn_origem", "v_msisdn_destino",
            "number", "contact", "contato", "phone", "mobile", "movel", "alvo", "interceptado", "interlocutor"
        ],
        "imei": [
            "imei", "terminal id", "terminal_id", "id", "equipamento", "aparelho", "device", "serial",
            "esn", "meid", "identificador_equipamento", "hardware", "equip"
        ]
    },
    "Dados de Contas Online (Google Location)": {
        "id_localizacao": ["location id", "obfuscated id", "id", "identifier", "locid", "gaia", "user_id"],
        "email": [
            "email", "conta google", "gmail", "conta", "e-mail", "endereco", "endereço", 
            "login", "user", "username", "usuario", "usuário", "mail", "address", "principal", "recovery"
        ],
        "hash": ["hash", "md5", "sha1", "sha256", "sha512", "checksum", "digest"]
    }
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
/* Esconder a lista nativa do file_uploader para evitar confusão com o limite de 3 arquivos */
[data-testid="stFileUploadDropzone"] + div {
    display: none;
}
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
        2. Envie todas as planilhas para a área "Adicionar Planilhas".
        3. O sistema identificará automaticamente Colunas de Origem/Destino/IMEI/E-mail.
        4. Clique em "Processar Dados e Cruzar".
    
        O sistema encontrará automaticamente dados que se repetem em arquivos diferentes no seu acervo.
        
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

# --- Upload de Arquivos ---

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {} # Dict de filename: file_object

st.header("Adicionar Planilhas")
new_files = st.file_uploader("Arraste ou selecione as planilhas aqui", type=["csv", "xlsx", "xls"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in st.session_state.uploaded_files:
            st.session_state.uploaded_files[f.name] = f

# Mostrar lista personalizada de arquivos (Até 20 por tela)
if st.session_state.uploaded_files:
    st.subheader(f"Arquivos no Acervo ({len(st.session_state.uploaded_files)})")
    
    arquivos_lista = sorted(list(st.session_state.uploaded_files.keys()))
    itens_por_pagina = 20
    
    if len(arquivos_lista) > itens_por_pagina:
        total_paginas = (len(arquivos_lista) // itens_por_pagina) + (1 if len(arquivos_lista) % itens_por_pagina > 0 else 0)
        pagina = st.number_input("Página da lista de arquivos", min_value=1, max_value=total_paginas, step=1)
        inicio = (pagina - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
    else:
        inicio, fim = 0, len(arquivos_lista)
        
    for fname in arquivos_lista[inicio:fim]:
        col_f, col_del = st.columns([5, 1])
        col_f.markdown(f"✅ `{fname}`")
        if col_del.button("❌", key=f"del_{fname}"):
            del st.session_state.uploaded_files[fname]
            st.rerun()
    
    if st.button("Limpar Todo o Acervo", type="secondary"):
        st.session_state.uploaded_files = {}
        st.rerun()

# --- Detectar Cabeçalho ---

def detectar_cabecalho(file, filename, max_linhas=15):
    try:
        file.seek(0)
        for i in range(max_linhas):
            file.seek(0)
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(file, header=i, nrows=10, encoding="utf-8", sep=None, engine='python')
            else:
                # Tentar ler com motores específicos para .xlsx e .xls
                if filename.lower().endswith(".xlsx"):
                    engine = 'openpyxl'
                elif filename.lower().endswith(".xls"):
                    engine = 'xlrd'
                else:
                    engine = None
                df = pd.read_excel(file, header=i, nrows=10, engine=engine)
            
            # Heurística: cabeçalho costuma ter poucas colunas nulas e nomes significativos
            column_names = [str(c) for c in df.columns]
            unnamed_count = sum(1 for c in column_names if "unnamed" in c.lower() or not c.strip())
            
            if df.shape[1] >= 2 and unnamed_count < df.shape[1] // 1.5:
                return i
        return 0
    except Exception:
        return 0

# --- Complementares ---

# Checar se há arquivos
if st.session_state.uploaded_files and data_types_to_process:

    if st.button("Processar Dados e Cruzar"):
        st.subheader("Status:")
        status_area = st.empty()
        progress = st.progress(0.0)
        dataframes_por_arquivo, erros = [], []
        contador = 0
        total_arquivos = len(st.session_state.uploaded_files)

        for nome_arquivo, file in st.session_state.uploaded_files.items():
            contador += 1
            status_area.text(f"Lendo: {nome_arquivo}")
            try:
                header_row = detectar_cabecalho(file, nome_arquivo)
                file.seek(0)
                if nome_arquivo.lower().endswith(".csv"):
                    df = pd.read_csv(file, header=header_row, dtype=str, encoding='utf-8', sep=None, engine='python')
                else:
                    if nome_arquivo.lower().endswith(".xlsx"):
                        engine = 'openpyxl'
                    elif nome_arquivo.lower().endswith(".xls"):
                        engine = 'xlrd'
                    else:
                        engine = None
                    df = pd.read_excel(file, header=header_row, dtype=str, engine=engine)
                
                # Limpeza inicial: remover 'nan'
                df = df.fillna("")
                # Standardizing columns
                df.columns = [str(col).strip().lower() for col in df.columns]
                dataframes_por_arquivo.append({"df": df, "nome": nome_arquivo})
            except Exception as e:
                erros.append(f"{nome_arquivo} -> Erro: {e}")
            progress.progress(contador / total_arquivos * 0.3)

        if len(dataframes_por_arquivo) < 1:
            st.error("Necessário ao menos um arquivo válido.")
        else:
            normalizadores = {
                "telefone": lambda x: normalizar_telefone(x, strict_mode),
                "imei": lambda x: normalizar_imei(x, strict_mode),
                "email": lambda x: normalizar_email(x, strict_mode),
                "hash": lambda x: normalizar_hash(x, strict_mode),
                "id_localizacao": lambda x: normalizar_id_localizacao(x, strict_mode)
            }
            map_primario = COLUNA_MAP_HEURISTICO[analysis_type]

            # Armazenar todos os dados extraídos com seus níveis de confiança
            todos_registros = []

            for bloco in dataframes_por_arquivo:
                df, nome_arquivo = bloco["df"], bloco["nome"]
                
                # Primeiro, vamos identificar as colunas para cada tipo de dado
                colunas_por_tipo = {}
                for tipo in data_types_to_process:
                    colunas_tipo = [col for col in df.columns if any(k in col.lower() for k in map_primario[tipo])]
                    
                    # NOVO: SE NÃO ENCONTRAR COLUNA PELO NOME, VARRE TUDO (Varredura de Segurança)
                    # Isso garante que mesmo que a planilha mude o nome da coluna para algo desconhecido, os dados serão capturados
                    if not colunas_tipo:
                        colunas_tipo = list(df.columns)
                    
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
                                    "arquivo": nome_arquivo,
                                    "valor_original": row[col],
                                    "coluna_fonte": col
                                }
                                todos_registros.append(dado)

            progress.progress(0.6)
            
            # Converter para DataFrame para facilitar o processamento
            df_todos = pd.DataFrame(todos_registros)
            
            if df_todos.empty:
                st.warning("Nenhum dado relevante encontrado nos arquivos.")
            else:
                # Filtrar por nível de confiança (usando todos os níveis por padrão)
                df_filtrado = df_todos[df_todos["confianca"].isin(niveis_confianca)]
                
                # Identificar cruzamentos
                cruzamentos = []
                for (valor, tipo), grupo in df_filtrado.groupby(["valor", "tipo"]):
                    arquivos_unicos = grupo["arquivo"].unique()
                    
                    # Cruzamento ocorre se o mesmo valor aparece em arquivos diferentes
                    if len(arquivos_unicos) > 1:
                        cruzamento = {
                            "valor": valor,
                            "tipo": tipo,
                            "confianca": grupo["confianca"].max(),
                            "arquivos": list(arquivos_unicos),
                            "colunas": list(grupo["coluna_fonte"].unique()),
                            "ocorrencias": len(grupo)
                        }
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
                        if st.download_button(
                            "📊 Baixar Planilha de Cruzamentos (XLSX)",
                            data=output_cruzamentos.getvalue(),
                            file_name="cruzamentos_telematicos.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        ):
                            st.session_state.uploaded_files = {}
                            st.success("Dados limpos com sucesso. Reiniciando...")
                            time.sleep(1)
                            st.rerun()
                    
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
                        if st.download_button(
                            "📄 Baixar Todos os Registros Extraídos (XLSX)",
                            data=output_todos.getvalue(),
                            file_name="todos_registros_extraidos.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        ):
                            st.session_state.uploaded_files = {}
                            st.success("Dados limpos com sucesso. Reiniciando...")
                            time.sleep(1)
                            st.rerun()
                    
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