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

# Inicializa a memória do sistema
if "nome_projeto" not in st.session_state:
    st.session_state.nome_projeto = None
if "etapas_manuais" not in st.session_state:
    st.session_state.etapas_manuais = []

# ==========================================
# 2. CONFIGURAÇÃO INTELIGENTE DA IA
# ==========================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Sistema de Descoberta Automática (Evita o Erro 404)
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

# ==========================================
# 3. FUNÇÕES DE RENDERIZAÇÃO E MATEMÁTICA
# ==========================================
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

def desenhar_grafico_da_memoria(orientacao, altura):
    if len(st.session_state.etapas_manuais) == 0:
        return
        
    tipo_grafico_mermaid = "graph TD" if "Vertical" in orientacao else "graph LR"
    codigo = f"{tipo_grafico_mermaid}\n"
    codigo += "classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;\n"
    codigo += "classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;\n"
    codigo += "classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;\n"
    codigo += "classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;\n"
    codigo += "classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;\n"

    for et in st.session_state.etapas_manuais:
        # Se por acaso vier uma linha vazia da tabela, ignora para não quebrar
        if not et or "id" not in et:
            continue
            
        if "<br/>" not in str(et["texto"]):
            palavras = str(et["texto"]).split()
            pedacos = [" ".join(palavras[i:i+4]) for i in range(0, len(palavras), 4)]
            texto_final = "<br/>".join(pedacos)
        else:
            texto_final = str(et["texto"])
        
        texto_final = texto_final.replace('"', "'") 
        
        if "Decisão" in str(et["tipo"]): 
            cx = f'{et["id"]}{{"{texto_final}"}}:::decisao'
        elif "Início" in str(et["tipo"]): 
            cx = f'{et["id"]}(["{texto_final}"]):::inicio'
        elif "Sucesso" in str(et["tipo"]): 
            cx = f'{et["id"]}(["{texto_final}"]):::sucesso'
        elif "Erro" in str(et["tipo"]): 
            cx = f'{et["id"]}(["{texto_final}"]):::erro'
        else: 
            cx = f'{et["id"]}["{texto_final}"]:::processo'
        
        codigo += f"    {cx}\n"
        
        if "proxima" in et and et["proxima"]:
            for ligacao in str(et["proxima"]).split(","):
                if ligacao: 
                    codigo += f'    {et["id"]} --> {ligacao.strip()}\n'

    renderizar_mermaid(codigo, orientacao, altura)

# ==========================================
# 4. TELA INICIAL (Boas-vindas)
# ==========================================
if st.session_state.nome_projeto is None:
    st.title("Bem-vindo ao Gerador de Fluxogramas 📊")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.write("### ✨ Novo Projeto")
        novo_nome = st.text_input("Qual será o nome deste projeto?", placeholder="Ex: Abertura de Contas")
        if st.button("Criar Área de Trabalho", type="primary"):
            if novo_nome.strip() != "":
                st.session_state.nome_projeto = novo_nome
                st.session_state.etapas_manuais = []
                st.rerun()
            else:
                st.warning("Por favor, digite um nome para o projeto.")
    with col2:
        st.write("### 📂 Continuar Projeto")
        arquivo = st.file_uploader("Suba o arquivo .json salvo:", type=["json"])
        if arquivo:
            if st.button("Abrir Projeto"):
                dados = json.load(arquivo)
                if isinstance(dados, dict):
                    st.session_state.nome_projeto = dados.get("nome", "Projeto Restaurado")
                    st.session_state.etapas_manuais = dados.get("etapas", [])
                else:
                    st.session_state.nome_projeto = "Projeto Restaurado"
                    st.session_state.etapas_manuais = dados
                st.rerun()

# ==========================================
# 5. ÁREA DE TRABALHO UNIFICADA
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
        altura_grafico = st.slider("Altura da Tela (Pixels):", 400, 3000, 1000, 100)

    st.write("Insira dados pela IA ou Lista Rápida. Depois, edite tudo diretamente na planilha abaixo!")

    # ABAS DE ENTRADA DE DADOS
    aba_ia, aba_lista, aba_editar, aba_salvar = st.tabs([
        "🤖 Injetar com Inteligência Artificial", 
        "📝 Importar Lista Rápida", 
        "➕ Adicionar Linha Avulsa", 
        "💾 Salvar Projeto"
    ])
    
    # ABA 1: IA
    with aba_ia:
        texto_usuario = st.text_area("Descreva o processo para a IA construir a base:", height=100)
        if st.button("✨ Gerar Base com IA", type="primary"):
            if texto_usuario.strip() != "":
                prompt_json = f"""
                Analise o processo abaixo e extraia as etapas para um fluxograma.
                Retorne APENAS um array JSON válido.
                Estrutura de cada objeto no array:
                - "id": Letras ou números sequenciais.
                - "texto": Resumo da ação (máximo 5 palavras).
                - "tipo": "Processo Comum", "Início / Fim", "Decisão", "Sucesso" ou "Erro".
                - "proxima": ID da próxima etapa.
                Processo: {texto_usuario}
                """
                try:
                    with st.spinner("A IA está estruturando as caixas..."):
                        resposta = modelo.generate_content(prompt_json)
                        texto_bruto = resposta.text
                        match = re.search(r'\[.*\]', texto_bruto, re.DOTALL)
                        if match:
                            st.session_state.etapas_manuais = json.loads(match.group(0))
                            st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")

    # ABA 2: LISTA RÁPIDA
    with aba_lista:
        lista_texto = st.text_area("Cole sua lista numerada aqui:", height=100)
        if st.button("⚡ Transformar Lista em Gráfico"):
            if lista_texto.strip() != "":
                linhas = [l.strip() for l in lista_texto.split("\n") if l.strip()]
                etapas_processadas = []
                for idx, Secret_linha in enumerate(linhas):
                    linha_limpa = re.sub(r'^\s*[0-9\s,e\–\-]+(?:-|\s|\.)\s*', '', Secret_linha).strip()
                    linha_limpa = linha_limpa.replace("(", " - ").replace(")", "")
                    id_atual = str(idx + 1)
                    proxima = str(idx + 2) if idx < len(linhas) - 1 else ""
                    tipo = "Processo Comum"
                    linha_lower = linha_limpa.lower()
                    is_inicio = ("inicio" in linha_lower) or ("início" in linha_lower)
                    is_fim = ("fim" in linha_lower[:5]) or ("encerra" in linha_lower)
                    if is_inicio or is_fim:
                        tipo = "Início / Fim"
                    elif ("?" in linha_lower) or ("se " in linha_lower) or ("selecionar" in linha_lower):
                        tipo = "Decisão"
                    elif ("erro" in linha_lower) or ("falha" in linha_lower) or ("rejeit" in linha_lower):
                        tipo = "Erro"
                    etapas_processadas.append({"id": id_atual, "texto": linha_limpa, "tipo": tipo, "proxima": proxima})
                st.session_state.etapas_manuais = etapas_processadas
                st.rerun()

    # ABA 3: ADICIONAR AVULSA
    with aba_editar:
        col1, col2 = st.columns(2)
        with col1:
            id_novo = st.text_input("ID do novo nó:").upper().strip()
            texto_novo = st.text_input("Texto do novo nó:")
        with col2:
            tipo_novo = st.selectbox("Tipo:", ["Processo Comum", "Início / Fim", "Decisão", "Sucesso", "Erro"])
            prox_novo = st.text_input("Próximo ID:")
        if st.button("➕ Inserir Linha na Planilha"):
            if id_novo and texto_novo:
                st.session_state.etapas_manuais.append({"id": id_novo, "texto": texto_novo, "tipo": tipo_novo, "proxima": prox_novo})
                st.rerun()

    # ABA 4: SALVAR
    with aba_salvar:
        if len(st.session_state.etapas_manuais) > 0:
            dados_completos = {"nome": st.session_state.nome_projeto, "etapas": st.session_state.etapas_manuais}
            st.download_button("💾 Backup do Projeto (.json)", json.dumps(dados_completos, indent=4), f"{st.session_state.nome_projeto.replace(' ', '_')}.json", "application/json", type="primary")

    # ==========================================
    # 6. A SUPER PLANILHA EDITÁVEL (A MÁGICA AQUI)
    # ==========================================
    if len(st.session_state.etapas_manuais) > 0:
        st.divider()
        colA, colB = st.columns([4, 1])
        with colA:
            st.write("#### 📊 Planilha de Controle Direto (Dê dois cliques para editar)")
        with colB:
            if st.button("💥 Limpar Tudo", use_container_width=True):
                st.session_state.etapas_manuais = []
                st.rerun()
        
        # O TRANSFORMATOR DE TABELA ESTÁTICA EM PLANILHA DINÂMICA
        tabela_editavel = st.data_editor(
            st.session_state.etapas_manuais,
            use_container_width=True,
            num_rows="dynamic", # Permite que você delete ou crie linhas direto na tabela!
            column_config={
                "id": st.column_config.TextColumn("ID do Nó", required=True),
                "texto": st.column_config.TextColumn("Texto da Caixa", required=True),
                "tipo": st.column_config.SelectboxColumn(
                    "Categoria (Cor)",
                    options=["Processo Comum", "Início / Fim", "Decisão", "Sucesso", "Erro"],
                    required=True
                ),
                "proxima": st.column_config.TextColumn("Liga ao ID (Separe por vírgula para bifurcar)")
            }
        )
        
        # Se você alterar qualquer letra na tabela, salva na memória e redesenha na hora!
        if tabela_editavel != st.session_state.etapas_manuais:
            st.session_state.etapas_manuais = tabela_editavel
            st.rerun()
            
        desenhar_grafico_da_memoria(orientacao, altura_grafico)
