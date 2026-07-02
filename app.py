import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import json
import re

# ==========================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gerador de Fluxogramas",
    page_icon="📊",
    layout="wide"
)

if "nome_projeto" not in st.session_state:
    st.session_state.nome_projeto = None
if "etapas_manuais" not in st.session_state:
    st.session_state.etapas_manuais = []

# Configuração da IA
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

modelo_valido = "gemini-1.5-flash"
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            modelo_valido = m.name
            if 'flash' in m.name:
                break
except:
    pass

modelo = genai.GenerativeModel(modelo_valido)

@st.cache_data(ttl=3600, show_spinner=False)
def gerar_grafico_ia(prompt):
    resposta = modelo.generate_content(prompt)
    return resposta.text.replace("```mermaid", "").replace("```", "").strip()

def renderizar_mermaid(codigo_mermaid, orientacao_tela, altura_tela):
    use_max_width = "false" if "Horizontal" in orientacao_tela else "true"
    html_mermaid = f"""
        <html>
        <head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
            <style>
                body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: transparent; }}
                .container {{ position: relative; width: 100%; height: 100%; }}
                .btn-download {{
                    position: absolute; top: 10px; right: 10px;
                    background-color: #1a237e; color: white; border: none;
                    padding: 9px 16px; font-size: 13px; font-weight: bold;
                    border-radius: 4px; cursor: pointer;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.15); z-index: 9999;
                }}
                .btn-download:hover {{ background-color: #0d1442; }}
            </style>
        </head>
        <body>
            <div class="container">
                <button class="btn-download" onclick="baixarFluxograma()">📥 Baixar Imagem (PNG)</button>
                <div class="mermaid">
                    {codigo_mermaid}
                </div>
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'null', flowchart: {{ useMaxWidth: {use_max_width}, htmlLabels: true }} }});
            </script>
            <script>
                function baixarFluxograma() {{
                    const svg = document.querySelector('.mermaid svg');
                    if (!svg) {{ alert('Aguarde o gráfico carregar.'); return; }}
                    const svgData = new XMLSerializer().serializeToString(svg);
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const img = new Image();
                    canvas.width = svg.getBoundingClientRect().width * 2;
                    canvas.height = svg.getBoundingClientRect().height * 2;
                    img.onload = function() {{
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        const a = document.createElement('a');
                        a.download = 'fluxograma.png';
                        a.href = canvas.toDataURL('image/png');
                        a.click();
                    }};
                    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
                }}
            </script>
        </body>
        </html>
    """
    components.html(html_mermaid, height=altura_tela, scrolling=True)

# ==========================================
# 3. TELA INICIAL
# ==========================================
if st.session_state.nome_projeto is None:
    st.title("Bem-vindo ao Gerador de Fluxogramas 📊")
    st.write("Crie diagramas profissionais com Inteligência Artificial ou construa manualmente passo a passo.")
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### ✨ Novo Projeto")
        novo_nome = st.text_input("Qual será o nome deste projeto?", placeholder="Ex: Fluxo de Transferegov")
        if st.button("Criar Área de Trabalho", type="primary"):
            if novo_nome.strip() != "":
                st.session_state.nome_projeto = novo_nome
                st.session_state.etapas_manuais = []
                st.rerun()
            else:
                st.warning("Por favor, digite um nome para o projeto.")
                
    with col2:
        st.write("### 📂 Continuar Projeto (Carregar)")
        arquivo_enviado = st.file_uploader("Suba o arquivo .json do seu projeto salvo:", type=["json"])
        if arquivo_enviado is not None:
            if st.button("Abrir Projeto"):
                try:
                    dados = json.load(arquivo_enviado)
                    if isinstance(dados, list):
                        st.session_state.nome_projeto = "Projeto Restaurado"
                        st.session_state.etapas_manuais = dados
                    else:
                        st.session_state.nome_projeto = dados.get("nome", "Projeto Sem Nome")
                        st.session_state.etapas_manuais = dados.get("etapas", [])
                    st.success("Projeto carregado!")
                    st.rerun()
                except:
                    st.error("Arquivo inválido.")

# ==========================================
# 4. ÁREA DE TRABALHO (WORKSPACE)
# ==========================================
else:
    col_titulo, col_sair = st.columns([4, 1])
    with col_titulo:
        st.title(f"📁 Projeto: {st.session_state.nome_projeto}")
    with col_sair:
        st.write("")
        if st.button("🚪 Fechar Projeto", use_container_width=True):
            st.session_state.nome_projeto = None
            st.session_state.etapas_manuais = []
            st.rerun()

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=70)
        st.title("Configurações")
        st.divider()
        orientacao = st.selectbox("Direção do Layout:", ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"])
        altura_grafico = st.slider("Altura da Tela (Pixels):", 400, 3000, 1000, 100) # Aumentei o máximo de altura para projetos gigantes
    
    tipo_grafico_mermaid = "graph TD" if "Vertical" in orientacao else "graph LR"

    modo_criacao = st.radio(
        "Modo de Criação:",
        ["🤖 Automático (Inteligência Artificial)", "⚙️ Manual (Construtor Passo a Passo)"],
        horizontal=True
    )
    st.divider()

    # --- MODO IA ---
    if "Automático" in modo_criacao:
        st.write("### Modo Inteligente")
        texto_usuario = st.text_area("Descreva o seu processo corrido aqui:", height=150)

        if st.button("Gerar Fluxograma por IA", type="primary"):
            if texto_usuario.strip() == "":
                st.warning("Por favor, insira a descrição.")
            else:
                prompt_secreto = f"""
                Você é um gerador de código Mermaid.js. Transforme o texto num diagrama '{tipo_grafico_mermaid}'.
                1. IDs: Use letras simples sequenciais (A, B, C...).
                2. Texto: Em aspas, sem parênteses. Quebre com <br/> a cada 4 palavras para não cortar.
                3. Aplique as classes e cole as definições de cores padrão.
                classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
                classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;
                classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;
                classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;
                classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;
                Retorne APENAS o código puro.
                Texto: {texto_usuario}
                """
                try:
                    with st.spinner("Desenhando..."):
                        codigo_gerado = gerar_grafico_ia(prompt_secreto)
                        renderizar_mermaid(codigo_gerado, orientacao, altura_grafico)
                except Exception as e:
                    st.error(f"Erro: {e}")

    # --- MODO MANUAL (LISTA RÁPIDA CORRIGIDA) ---
    else:
        st.write("### Modo Construtor")
        
        aba_lista, aba_inserir, aba_remover, aba_salvar = st.tabs([
            "📝 Colar Lista Rápida (Recomendado)", 
            "➕ Adicionar / Editar Individual", 
            "❌ Apagar Etapa", 
            "💾 Salvar Trabalho"
        ])
        
        with aba_lista:
            st.write("Cole a sua lista de ações. A nova versão fatiará o texto automaticamente para as caixas ficarem proporcionais.")
            lista_texto = st.text_area("Cole sua lista de etapas aqui:", height=180)
            
            if st.button("⚡ Transformar Lista em Fluxograma", type="primary"):
                if lista_texto.strip() != "":
                    linhas = [l.strip() for l in lista_texto.split("\n") if l.strip()]
                    etapas_processadas = []
                    
                    for idx, linha in enumerate(linhas):
                        # NOVA REGEX BLINDADA: Tira números simples "1-" e números em grupo "19, 20 e 21 -"
                        linha_limpa = re.sub(r'^\s*[0-9\s,e\–\-]+(?:-|\s|\.)\s*', '', linha).strip()
                        linha_limpa = linha_limpa.replace("(", " - ").replace(")", "")
                        
                        id_atual = str(idx + 1)
                        proxima = str(idx + 2) if idx < len(linhas) - 1 else ""
                        
                        tipo = "Processo Comum"
                        linha_lower = linha_limpa.lower()
                        if "inicio" in linha_lower or "início" in linha_lower:
                            tipo = "Início / Fim"
                        elif "fim" in list(linha_lower)[:5] or "encerra" in linha_lower:
                            tipo = "Início / Fim"
                        elif "?" in linha_lower or "se " in linha_lower or "selecionar" in linha_lower:
                            tipo = "Decisão"
                        elif "erro" in linha_lower or "falha" in linha_lower or "rejeit" in linha_lower:
                            tipo = "Erro"
                        
                        etapas_processadas.append({"id": id_atual, "texto": linha_limpa, "tipo": tipo, "proxima": proxima})
                    
                    st.session_state.etapas_manuais = etapas_processadas
                    st.success("Lista processada sem quebrar o layout!")
                    st.rerun()
                else:
                    st.warning("Cole uma lista de texto primeiro.")

        with aba_inserir:
            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                id_etapa = st.text_input("ID da Caixa (Ex: 1 ou 2)").upper().strip()
            with col2:
                texto_etapa = st.text_input("Texto da Ação:")
            with col3:
                tipo_etapa = st.selectbox("Categoria:", ["Processo Comum", "Início / Fim", "Decisão", "Sucesso", "Erro"])
            proxima_ligacao = st.text_input("Liga ao ID: (Separe por vírgulas, ex: 3, 4)").upper().replace(" ", "")

            if st.button("💾 Gravar Ajuste na Etapa"):
                if id_etapa and texto_etapa:
                    id_existente = False
                    for i, etapa in enumerate(st.session_state.etapas_manuais):
                        if etapa["id"] == id_etapa:
                            st.session_state.etapas_manuais[i] = {"id": id_etapa, "texto": texto_etapa, "tipo": tipo_etapa, "proxima": proxima_ligacao}
                            id_existente = True
                            break
                    if not id_existente:
                        st.session_state.etapas_manuais.append({"id": id_etapa, "texto": texto_etapa, "tipo": tipo_etapa, "proxima": proxima_ligacao})
                    st.rerun()

        with aba_remover:
            id_para_remover = st.text_input("ID para remover:", max_chars=3).upper().strip()
            if st.button("🗑️ Apagar Etapa"):
                st.session_state.etapas_manuais = [et for et in st.session_state.etapas_manuais if et["id"] != id_para_remover]
                st.rerun()

        with aba_salvar:
            if len(st.session_state.etapas_manuais) > 0:
                dados_completos = {"nome": st.session_state.nome_projeto, "etapas": st.session_state.etapas_manuais}
                st.download_button(
                    label="💾 Fazer Backup do Projeto (.json)",
                    data=json.dumps(dados_completos, indent=4),
                    file_name=f"{st.session_state.nome_projeto.replace(' ', '_')}.json",
                    mime="application/json",
                    type="primary"
                )

        # -------------------------------------------------------------
        # RENDERIZAÇÃO MATEMÁTICA QUE FATIA FRASES GIGANTES (A SOLUÇÃO)
        # -------------------------------------------------------------
        if len(st.session_state.etapas_manuais) > 0:
            st.divider()
            st.write("#### 📋 Painel de Edição e Pré-visualização")
            st.dataframe(st.session_state.etapas_manuais, use_container_width=True)
            
            if st.button("💥 Resetar Todo o Fluxo"):
                st.session_state.etapas_manuais = []
                st.rerun()

            codigo_manual = f"{tipo_grafico_mermaid}\n"
            codigo_manual += "classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;\n"
            codigo_manual += "classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;\n"
            codigo_manual += "classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;\n"
            codigo_manual += "classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;\n"
            codigo_manual += "classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;\n"

            for et in st.session_state.etapas_manuais:
                # O NOVO FATIADOR DE FRASES (Quebra a cada 4 palavras repetidamente)
                if "<br/>" not in et["texto"]:
                    palavras = et["texto"].split()
                    pedacos = [" ".join(palavras[i:i+4]) for i in range(0, len(palavras), 4)]
                    texto_final = "<br/>".join(pedacos)
                else:
                    texto_final = et["texto"]
                
                texto_final = texto_final.replace('"', "'") # Tira aspas duplas que quebram código
                
                if "Decisão" in et["tipo"]: cx = f'{et["id"]}{{"{texto_final}"}}:::decisao'
                elif "Início" in et["tipo"]: cx = f'{et["id"]}(["{texto_final}"]):::inicio'
                elif "Sucesso" in et["tipo"]: cx = f'{et["id"]}(["{texto_final}"]):::sucesso'
                elif "Erro" in et["tipo"]: cx = f'{et["id"]}(["{texto_final}"]):::erro'
                else: cx = f'{et["id"]}["{texto_final}"]:::processo'
                
                codigo_manual += f"    {cx}\n"
                
                if et["proxima"]:
                    for ligacao in et["proxima"].split(","):
                        if ligacao: codigo_manual += f'    {et["id"]} --> {ligacao.strip()}\n'

            renderizar_mermaid(codigo_manual, orientacao, altura_grafico)
