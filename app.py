import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# ==========================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gerador de Fluxogramas",
    page_icon="📊",
    layout="wide"
)

# Inicializa a memória para o Modo Manual
if "etapas_manuais" not in st.session_state:
    st.session_state.etapas_manuais = []

# Configuração da IA (só faz a conexão se for usar)
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

# Função de Cache para poupar a cota gratuita do Google
@st.cache_data(ttl=3600, show_spinner=False)
def gerar_grafico_ia(prompt):
    resposta = modelo.generate_content(prompt)
    return resposta.text.replace("```mermaid", "").replace("```", "").strip()

# ==========================================
# 2. FUNÇÃO CENTRAL DE RENDERIZAÇÃO E DESIGN
# ==========================================
# Esta função desenha o gráfico na tela, não importa se veio da IA ou do Manual
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
                mermaid.initialize({{ 
                    startOnLoad: true, 
                    theme: 'null',
                    flowchart: {{ useMaxWidth: {use_max_width}, htmlLabels: true }}
                }});
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
                        a.download = 'fluxograma_profissional.png';
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
# 3. BARRA LATERAL (CONFIGURAÇÕES GERAIS)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=70)
    st.title("Configurações")
    st.write("Ajuste a visualização do gráfico.")
    st.divider()
    
    orientacao = st.selectbox("Direção do Layout:", ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"])
    altura_grafico = st.slider("Altura da Tela (Pixels):", 400, 2000, 700, 100)

tipo_grafico_mermaid = "graph TD" if "Vertical" in orientacao else "graph LR"


# ==========================================
# 4. ÁREA PRINCIPAL: ESCOLHA DO MODO
# ==========================================
st.title("Plataforma de Fluxogramas 📊")

# O utilizador escolhe a engine logo de cara
modo_criacao = st.radio(
    "Escolha o motor de criação:",
    ["🤖 Automático (Inteligência Artificial)", "⚙️ Manual (Construtor Passo a Passo)"],
    horizontal=True
)

st.divider()

# ---------------------------------------------------------
# MODO 1: INTELIGÊNCIA ARTIFICIAL
# ---------------------------------------------------------
if "Automático" in modo_criacao:
    st.write("### Modo Inteligente")
    st.write("Descreva o processo corrido e deixe a IA cuidar da lógica e do design.")
    
    texto_usuario = st.text_area("Descreva o seu processo aqui:", height=150, placeholder="Ex: O utilizador acede ao sistema...")

    if st.button("Gerar Fluxograma por IA", type="primary"):
        if texto_usuario.strip() == "":
            st.warning("Por favor, insira a descrição de um processo.")
        else:
            prompt_secreto = f"""
            Você é um gerador de código Mermaid.js. Transforme o texto num diagrama '{tipo_grafico_mermaid}'.
            1. IDs: Use letras simples sequenciais (A, B, C).
            2. Texto em aspas e sem parênteses brutos. Quebre linhas com <br/> a cada 3 palavras.
            3. Classes:
               - Início/Fim: ID([Texto]):::inicio
               - Processos: ID[Texto]:::processo
               - Decisões: ID{{Texto}}:::decisao
               - Sucesso: ID([Texto]):::sucesso
               - Erros: ID([Texto]):::erro
            
            COLE ISTO NO FINAL:
            classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
            classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;
            classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;
            classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;
            classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;
            
            Retorne APENAS o código.
            Texto: {texto_usuario}
            """
            
            try:
                with st.spinner("A Inteligência Artificial está a desenhar o fluxo..."):
                    codigo_gerado = gerar_grafico_ia(prompt_secreto)
                    
                    with st.expander("⚙️ Ver Código Fonte"):
                        st.code(codigo_gerado, language="mermaid")
                    
                    renderizar_mermaid(codigo_gerado, orientacao, altura_grafico)
                    
            except Exception as e:
                erro_str = str(e)
                if "429" in erro_str or "quota" in erro_str.lower():
                    st.warning("⏳ Limite de requisições gratuitas atingido. Aguarde 1 minuto e tente de novo!")
                else:
                    st.error(f"Erro na IA: {e}")

# ---------------------------------------------------------
# MODO 2: CONSTRUTOR MANUAL (SEM IA, SEM LIMITES)
# ---------------------------------------------------------
else:
    st.write("### Modo Construtor (100% Gratuito)")
    st.write("Crie o fluxo adicionando as etapas e ligando-as pelo ID. Perfeito para contornar limites de IA.")
    
    col1, col2, col3 = st.columns([1, 3, 2])
    with col1:
        id_etapa = st.text_input("ID (Ex: A)", max_chars=2).upper().strip()
    with col2:
        texto_etapa = st.text_input("Texto da Ação (Ex: Emitir nota)")
    with col3:
        tipo_etapa = st.selectbox(
            "Categoria da Ação:", 
            ["Processo Comum (Verde-água)", "Início ou Fim (Azul)", "Decisão / Pergunta (Laranja)", "Sucesso (Verde)", "Erro / Falha (Vermelho)"]
        )
    
    col4, col5 = st.columns([4, 2])
    with col4:
        st.caption("Dica: Use <br/> no texto da ação se a frase for muito longa para quebrar a linha.")
    with col5:
        # Permite separar por vírgula se uma etapa for ligar a duas (ex: uma decisão ligando a B e C)
        proxima_ligacao = st.text_input("Liga ao ID: (Opcional, ex: B)").upper().replace(" ", "")

    if st.button("➕ Inserir Etapa"):
        if id_etapa and texto_etapa:
            st.session_state.etapas_manuais.append({
                "id": id_etapa,
                "texto": texto_etapa,
                "tipo": tipo_etapa,
                "proxima": proxima_ligacao
            })
        else:
            st.warning("Preencha o ID e o Texto antes de inserir.")

    # Se já existirem etapas, desenha a tela e monta o código na hora
    if len(st.session_state.etapas_manuais) > 0:
        st.divider()
        colA, colB = st.columns([4, 1])
        with colA:
            st.write("#### 🛠️ Pré-visualização do Fluxo")
        with colB:
            if st.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.etapas_manuais = []
                st.rerun()

        # Construção da lógica Mermaid via Python (Sem IA)
        codigo_manual = f"{tipo_grafico_mermaid}\n"
        
        # Injeta as classes de cores para o modo manual ficar igual ao da IA
        codigo_manual += "classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;\n"
        codigo_manual += "classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;\n"
        codigo_manual += "classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;\n"
        codigo_manual += "classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;\n"
        codigo_manual += "classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;\n"

        for et in st.session_state.etapas_manuais:
            texto_limpo = et["texto"].replace('"', "'") # Proteção contra quebras
            
            # Define o formato e a cor baseado na escolha
            if "Decisão" in et["tipo"]:
                caixa = f'{et["id"]}{{"{texto_limpo}"}}:::decisao'
            elif "Início" in et["tipo"]:
                caixa = f'{et["id"]}(["{texto_limpo}"]):::inicio'
            elif "Sucesso" in et["tipo"]:
                caixa = f'{et["id"]}(["{texto_limpo}"]):::sucesso'
            elif "Erro" in et["tipo"]:
                caixa = f'{et["id"]}(["{texto_limpo}"]):::erro'
            else:
                caixa = f'{et["id"]}["{texto_limpo}"]:::processo'
                
            codigo_manual += f"    {caixa}\n"
            
            # Se houver ligação, cria as setas (separa por vírgula para bifurcações)
            if et["proxima"]:
                ligacoes = et["proxima"].split(",")
                for ligacao in ligacoes:
                    if ligacao:
                        codigo_manual += f'    {et["id"]} --> {ligacao}\n'

        with st.expander("⚙️ Ver Código Fonte Gerado Manualmente"):
            st.code(codigo_manual, language="mermaid")

        # Chama a mesma função de renderização usada pela IA
        renderizar_mermaid(codigo_manual, orientacao, altura_grafico)
