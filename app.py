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
modelo = genai.GenerativeModel("gemini-1.5-flash")

# ==========================================
# 2. FUNÇÕES DE RENDERIZAÇÃO
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
        if "<br/>" not in et["texto"]:
            palavras = et["texto"].split()
            pedacos = [" ".join(palavras[i:i+4]) for i in range(0, len(palavras), 4)]
            texto_final = "<br/>".join(pedacos)
        else:
            texto_final = et["texto"]
        
        texto_final = texto_final.replace('"', "'") 
        
        if "Decisão" in et["tipo"]: cx = f'{et["id"]}{{"{texto_final}"}}:::decisao'
        elif "Início" in et["tipo"]: cx = f'{et["id"]}(["{texto_final}"]):::inicio'
        elif "Sucesso" in et["tipo"]: cx = f'{et["id"]}(["{texto_final}"]):::sucesso'
        elif "Erro" in et["tipo"]: cx = f'{et["id"]}(["{texto_final}"]):::erro'
        else: cx = f'{et["id"]}["{texto_final}"]:::processo'
        
        codigo += f"    {cx}\n"
        
        if et["proxima"]:
            for ligacao in et["proxima"].split(","):
                if ligacao: codigo += f'    {et["id"]} --> {ligacao.strip()}\n'

    renderizar_mermaid(codigo, orientacao, altura)

# ==========================================
# 3. TELA INICIAL
# ==========================================
if st.session_state.nome_projeto is None:
    st.title("Bem-vindo ao Gerador de Fluxogramas 📊")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.write("### ✨ Novo Projeto")
        novo_nome = st.text_input("Qual será o nome deste projeto?")
        if st.button("Criar Área de Trabalho", type="primary"):
            if novo_nome.strip() != "":
                st.session_state.nome_projeto = novo_nome
                st.session_state.etapas_manuais = []
                st.rerun()
    with col2:
        st.write("### 📂 Continuar Projeto")
        arquivo = st.file_uploader("Suba o arquivo .json salvo:", type=["json"])
        if arquivo:
            if st.button("Abrir Projeto"):
                dados = json.load(arquivo)
                st.session_state.nome_projeto = dados.get("nome", "Projeto Restaurado") if isinstance(dados, dict) else "Projeto Restaurado"
                st.session_state.etapas_manuais = dados.get("etapas", dados) if isinstance(dados, dict) else dados
                st.rerun()

# ==========================================
# 4. ÁREA DE TRABALHO UNIFICADA
# ==========================================
else:
    # --- CABEÇALHO ---
    col_titulo, col_sair = st.columns([4, 1])
    with col_titulo:
        st.title(f"📁 Projeto: {st.session_state.nome_projeto}")
    with col_sair:
        st.write("")
        if st.button("🚪 Fechar Projeto", use_container_width=True):
            st.session_state.nome_projeto = None
            st.session_state.etapas_manuais = []
            st.rerun()

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=70)
        st.title("Configurações")
        st.divider()
        orientacao = st.selectbox("Direção do Layout:", ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"])
        altura_grafico = st.slider("Altura da Tela (Pixels):", 400, 3000, 1000, 100)

    st.write("Escolha uma ferramenta abaixo para inserir dados. O gráfico será atualizado em tempo real no final da página.")

    # --- FERRAMENTAS EM ABAS (TUDO NO MESMO ECRÃ) ---
    aba_ia, aba_lista, aba_editar, aba_remover, aba_salvar = st.tabs([
        "🤖 Gerar com Inteligência Artificial", 
        "📝 Colar Lista Rápida", 
        "✏️ Editar / Adicionar Etapa", 
        "❌ Apagar", 
        "💾 Salvar Projeto"
    ])
    
    # FERRAMENTA 1: IA
    with aba_ia:
        st.write("Descreva o seu processo corrido aqui. A IA vai montar o gráfico pronto para edição manual.")
        texto_usuario = st.text_area("Descreva o processo para a IA:", height=100)

        if st.button("✨ Gerar Base com IA", type="primary"):
            if texto_usuario.strip() != "":
                prompt_json = f"""
                Analise o processo abaixo e extraia as etapas para um fluxograma.
                Retorne APENAS um array JSON válido.
                Estrutura de cada objeto no array:
                - "id": Letras sequenciais (A, B, C...)
                - "texto": Resumo da ação (máximo 5 palavras).
                - "tipo": "Processo Comum", "Início / Fim", "Decisão", "Sucesso" ou "Erro".
                - "proxima": ID da próxima etapa (separe por vírgula se for decisão, deixe "" se for fim).
                Processo: {texto_usuario}
                """
                try:
                    with st.spinner("A IA está desenhando as caixas e conexões..."):
                        resposta = modelo.generate_content(prompt_json)
                        texto_limpo = resposta.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.etapas_manuais = json.loads(texto_limpo)
                        st.rerun()
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        st.warning("⏳ Limite gratuito atingido. Aguarde 1 minuto.")
                    else:
                        st.error("Erro ao gerar. Tente reescrever o texto.")
            else:
                st.warning("Insira a descrição.")

    # FERRAMENTA 2: LISTA RÁPIDA
    with aba_lista:
        lista_texto = st.text_area("Cole sua lista numerada de etapas aqui:", height=100)
        if st.button("⚡ Transformar Lista em Gráfico"):
            if lista_texto.strip() != "":
                linhas = [l.strip() for l in lista_texto.split("\n") if l.strip()]
                etapas_processadas = []
                for idx, linha in enumerate(linhas):
                    linha_limpa = re.sub(r'^\s*[0-9\s,e\–\-]+(?:-|\s|\.)\s*', '', linha).strip()
                    linha_limpa = linha_limpa.replace("(", " - ").replace(")", "")
                    id_atual = str(idx + 1)
                    proxima = str(idx + 2) if idx < len(linhas) - 1 else ""
                    tipo = "Processo Comum"
                    linha_lower = linha_limpa.lower()
                    if "inicio" in linha_lower or "início" in linha_lower or "fim" in list(linha_lower)[:5] or "encerra" in linha_lower: tipo = "Início / Fim"
                    elif "?" in linha_lower or "se " in linha_lower or "selecionar" in linha_lower: tipo = "Decisão"
                    elif "erro" in linha_lower or "falha" in linha_lower or "rejeit" in linha_lower: tipo = "Erro"
                    etapas_processadas.append({"id": id_atual, "texto": linha_limpa, "tipo": tipo, "proxima": proxima})
                st.session_state.etapas_manuais = etapas_processadas
                st.rerun()

    # FERRAMENTA 3: EDITOR INDIVIDUAL
    with aba_editar:
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            id_etapa = st.text_input("ID (Ex: A ou 1)").upper().strip()
        with col2:
            texto_etapa = st.text_input("Texto da Ação:")
        with col3:
            tipo_etapa = st.selectbox("Categoria da Cor:", ["Processo Comum", "Início / Fim", "Decisão", "Sucesso", "Erro"])
        proxima_ligacao = st.text_input("Liga ao ID: (Separe por vírgulas)").upper().replace(" ", "")

        if st.button("💾 Inserir ou Atualizar Etapa"):
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

    # FERRAMENTA 4: APAGAR
    with aba_remover:
        id_para_remover = st.text_input("ID para remover:").upper().strip()
        if st.button("🗑️ Apagar Etapa"):
            st.session_state.etapas_manuais = [et for et in st.session_state.etapas_manuais if et["id"] != id_para_remover]
            st.rerun()

    # FERRAMENTA 5: BACKUP
    with aba_salvar:
        if len(st.session_state.etapas_manuais) > 0:
            dados_completos = {"nome": st.session_state.nome_projeto, "etapas": st.session_state.etapas_manuais}
            st.download_button("💾 Backup do Projeto (.json)", json.dumps(dados_completos, indent=4), f"{st.session_state.nome_projeto.replace(' ', '_')}.json", "application/json", type="primary")

    # ==========================================
    # 5. O GRÁFICO E A TABELA (SEMPRE VISÍVEIS)
    # ==========================================
    if len(st.session_state.etapas_manuais) > 0:
        st.divider()
        colA, colB = st.columns([4, 1])
        with colA:
            st.write("#### 📋 O Seu Fluxograma")
        with colB:
            if st.button("💥 Limpar Tudo", use_container_width=True):
                st.session_state.etapas_manuais = []
                st.rerun()
        
        # Mostra a tabela e o gráfico um debaixo do outro, fixos na tela!
        with st.expander("Ver Tabela de Dados"):
            st.dataframe(st.session_state.etapas_manuais, use_container_width=True)
            
        desenhar_grafico_da_memoria(orientacao, altura_grafico)
