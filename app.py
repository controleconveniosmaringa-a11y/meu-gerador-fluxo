import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import json

# ==========================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gerador de Fluxogramas",
    page_icon="📊",
    layout="wide"
)

# Inicializa a memória principal do sistema
if "nome_projeto" not in st.session_state:
    st.session_state.nome_projeto = None
if "etapas_manuais" not in st.session_state:
    st.session_state.etapas_manuais = []

# ==========================================
# 2. CONFIGURAÇÃO DA IA E FUNÇÕES (Escondidas no fundo)
# ==========================================
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
                        a.download = 'meu_fluxograma.png';
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
# 3. TELA INICIAL (SPLASH SCREEN)
# ==========================================
# Se não houver nome do projeto, mostra a tela de boas-vindas bloqueando o resto
if st.session_state.nome_projeto is None:
    st.title("Bem-vindo ao Gerador de Fluxogramas 📊")
    st.write("Crie diagramas profissionais com Inteligência Artificial ou construa manualmente passo a passo.")
    st.divider()
    
    col1, col2 = st.columns(2)
    
    # OPÇÃO 1: CRIAR UM PROJETO DO ZERO
    with col1:
        st.write("### ✨ Novo Projeto")
        novo_nome = st.text_input("Qual será o nome deste projeto?", placeholder="Ex: Fluxo de Contratação RH")
        if st.button("Criar Área de Trabalho", type="primary"):
            if novo_nome.strip() != "":
                st.session_state.nome_projeto = novo_nome
                st.session_state.etapas_manuais = []
                st.rerun() # Atualiza a página para entrar na área de trabalho
            else:
                st.warning("Por favor, digite um nome para o projeto.")
                
    # OPÇÃO 2: CARREGAR PROJETO SALVO NO COMPUTADOR
    with col2:
        st.write("### 📂 Continuar Projeto (Carregar)")
        arquivo_enviado = st.file_uploader("Suba o arquivo .json do seu projeto salvo:", type=["json"])
        if arquivo_enviado is not None:
            if st.button("Abrir Projeto"):
                try:
                    dados = json.load(arquivo_enviado)
                    # O sistema aceita dados antigos (só lista) ou o novo formato estruturado
                    if isinstance(dados, list):
                        st.session_state.nome_projeto = "Projeto Restaurado"
                        st.session_state.etapas_manuais = dados
                    else:
                        st.session_state.nome_projeto = dados.get("nome", "Projeto Sem Nome")
                        st.session_state.etapas_manuais = dados.get("etapas", [])
                    st.success("Projeto carregado! Entrando na área de trabalho...")
                    st.rerun()
                except Exception as e:
                    st.error("Arquivo inválido ou corrompido.")

# ==========================================
# 4. ÁREA DE TRABALHO (WORKSPACE PRINCIPAL)
# ==========================================
# O código abaixo só aparece se o usuário já tiver escolhido o nome do projeto
else:
    # Cabeçalho do Projeto
    col_titulo, col_sair = st.columns([4, 1])
    with col_titulo:
        st.title(f"📁 Projeto: {st.session_state.nome_projeto}")
    with col_sair:
        st.write("") # Espaço para alinhar verticalmente
        if st.button("🚪 Fechar Projeto", use_container_width=True):
            st.session_state.nome_projeto = None
            st.session_state.etapas_manuais = []
            st.rerun()

    # Barra lateral de configurações
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=70)
        st.title("Configurações")
        st.divider()
        orientacao = st.selectbox("Direção do Layout:", ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"])
        altura_grafico = st.slider("Altura da Tela (Pixels):", 400, 2000, 700, 100)
    
    tipo_grafico_mermaid = "graph TD" if "Vertical" in orientacao else "graph LR"

    modo_criacao = st.radio(
        "Modo de Criação:",
        ["🤖 Automático (Inteligência Artificial)", "⚙️ Manual (Construtor Passo a Passo)"],
        horizontal=True
    )
    st.divider()

    # --- MODO 1: INTELIGÊNCIA ARTIFICIAL ---
    if "Automático" in modo_criacao:
        st.write("### Modo Inteligente")
        texto_usuario = st.text_area("Descreva o seu processo aqui:", height=150)

        if st.button("Gerar Fluxograma por IA", type="primary"):
            if texto_usuario.strip() == "":
                st.warning("Por favor, insira a descrição.")
            else:
                prompt_secreto = f"""
                Você é um gerador de código Mermaid.js. Transforme o texto num diagrama '{tipo_grafico_mermaid}'.
                1. IDs: Use letras simples.
                2. Texto: Em aspas, sem parênteses. Quebre com <br/>.
                3. Aplique as classes e cole as definições de cores padrão.
                classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
                classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;
                classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;
                classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;
                classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;
                Retorne APENAS o código.
                Texto: {texto_usuario}
                """
                try:
                    with st.spinner("Desenhando..."):
                        codigo_gerado = gerar_grafico_ia(prompt_secreto)
                        renderizar_mermaid(codigo_gerado, orientacao, altura_grafico)
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        st.warning("⏳ Limite gratuito atingido. Aguarde 1 minuto e tente de novo.")
                    else:
                        st.error(f"Erro: {e}")

    # --- MODO 2: CONSTRUTOR MANUAL E GESTÃO DE ARQUIVOS ---
    else:
        st.write("### Modo Construtor")
        
        aba_inserir, aba_remover, aba_salvar = st.tabs(["➕ Gerenciar Etapas", "❌ Apagar Etapa", "💾 Salvar Trabalho"])
        
        with aba_inserir:
            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                id_etapa = st.text_input("ID (Ex: A)", max_chars=2).upper().strip()
            with col2:
                texto_etapa = st.text_input("Texto da Ação:")
            with col3:
                tipo_etapa = st.selectbox("Categoria:", ["Processo Comum", "Início / Fim", "Decisão", "Sucesso", "Erro"])
            proxima_ligacao = st.text_input("Liga ao ID: (Opcional)").upper().replace(" ", "")

            if st.button("💾 Adicionar / Atualizar Etapa", type="primary"):
                if id_etapa and texto_etapa:
                    id_existente = False
                    for i, etapa in enumerate(st.session_state.etapas_manuais):
                        if etapa["id"] == id_etapa:
                            st.session_state.etapas_manuais[i] = {"id": id_etapa, "texto": texto_etapa, "tipo": tipo_etapa, "proxima": proxima_ligacao}
                            id_existente = True
                            st.success("Etapa editada!")
                            break
                    if not id_existente:
                        st.session_state.etapas_manuais.append({"id": id_etapa, "texto": texto_etapa, "tipo": tipo_etapa, "proxima": proxima_ligacao})
                        st.success("Etapa criada!")
                    st.rerun()
                else:
                    st.warning("Preencha o ID e o Texto.")

        with aba_remover:
            id_para_remover = st.text_input("ID para remover (Ex: B):", max_chars=2).upper().strip()
            if st.button("🗑️ Apagar Etapa"):
                lista_nova = [et for et in st.session_state.etapas_manuais if et["id"] != id_para_remover]
                if len(lista_nova) < len(st.session_state.etapas_manuais):
                    st.session_state.etapas_manuais = lista_nova
                    st.rerun()

        with aba_salvar:
            st.write(f"Baixe o arquivo de backup para não perder o projeto **{st.session_state.nome_projeto}** se fechar o site!")
            if len(st.session_state.etapas_manuais) > 0:
                # Agora o JSON guarda o nome do projeto e os dados juntos
                dados_completos = {
                    "nome": st.session_state.nome_projeto,
                    "etapas": st.session_state.etapas_manuais
                }
                projeto_json = json.dumps(dados_completos, indent=4)
                st.download_button(
                    label="💾 Fazer Backup do Projeto (.json)",
                    data=projeto_json,
                    file_name=f"{st.session_state.nome_projeto.replace(' ', '_')}.json",
                    mime="application/json",
                    type="primary"
                )

        # Renderização do gráfico manual
        if len(st.session_state.etapas_manuais) > 0:
            st.divider()
            st.write("#### 📋 Controle e Pré-visualização")
            st.dataframe(st.session_state.etapas_manuais, use_container_width=True)
            
            codigo_manual = f"{tipo_grafico_mermaid}\n"
            codigo_manual += "classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;\n"
            codigo_manual += "classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;\n"
            codigo_manual += "classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;\n"
            codigo_manual += "classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;\n"
            codigo_manual += "classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;\n"

            for et in st.session_state.etapas_manuais:
                texto = et["texto"].replace('"', "'")
                if "Decisão" in et["tipo"]: cx = f'{et["id"]}{{"{texto}"}}:::decisao'
                elif "Início" in et["tipo"]: cx = f'{et["id"]}(["{texto}"]):::inicio'
                elif "Sucesso" in et["tipo"]: cx = f'{et["id"]}(["{texto}"]):::sucesso'
                elif "Erro" in et["tipo"]: cx = f'{et["id"]}(["{texto}"]):::erro'
                else: cx = f'{et["id"]}["{texto}"]:::processo'
                
                codigo_manual += f"    {cx}\n"
                if et["proxima"]:
                    for ligacao in et["proxima"].split(","):
                        if ligacao: codigo_manual += f'    {et["id"]} --> {ligacao.strip()}\n'

            renderizar_mermaid(codigo_manual, orientacao, altura_grafico)
