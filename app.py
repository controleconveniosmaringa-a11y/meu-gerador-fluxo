import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
st.set_page_config(
    page_title="Gerador de Fluxogramas",
    page_icon="📊",
    layout="wide"
)

# Inicializa a memória para o Modo Manual
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

# 2. FUNÇÃO CENTRAL DE RENDERIZAÇÃO
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


# 3. BARRA LATERAL
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=70)
    st.title("Configurações")
    st.write("Ajuste a visualização do gráfico.")
    st.divider()
    
    orientacao = st.selectbox("Direção do Layout:", ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"])
    altura_grafico = st.slider("Altura da Tela (Pixels):", 400, 2000, 700, 100)

tipo_grafico_mermaid = "graph TD" if "Vertical" in orientacao else "graph LR"


# 4. ÁREA PRINCIPAL
st.title("Plataforma de Fluxogramas 📊")

modo_criacao = st.radio(
    "Escolha o motor de criação:",
    ["🤖 Automático (Inteligência Artificial)", "⚙️ Manual (Construtor Passo a Passo)"],
    horizontal=True
)

st.divider()

# --- MODO 1: IA ---
if "Automático" in modo_criacao:
    st.write("### Modo Inteligente")
    texto_usuario = st.text_area("Descreva o seu processo aqui:", height=150)

    if st.button("Gerar Fluxograma por IA", type="primary"):
        if texto_usuario.strip() == "":
            st.warning("Por favor, insira a descrição de um processo.")
        else:
            prompt_secreto = f"Seu prompt de IA padrão aqui... Texto: {texto_usuario}"
            try:
                with st.spinner("Desenhando..."):
                    codigo_gerado = gerar_grafico_ia(prompt_secreto)
                    renderizar_mermaid(codigo_gerado, orientacao, altura_grafico)
            except Exception as e:
                st.error(f"Erro: {e}")

# --- MODO 2: CONSTRUTOR MANUAL (COM FUNÇÃO EDITAR E REMOVER) ---
else:
    st.write("### Modo Construtor (100% Gratuito)")
    
    # Criamos abas para organizar a inserção/edição da remoção
    aba_inserir, aba_remover = st.tabs(["➕ Adicionar / Editar Etapa", "❌ Remover Etapa Específica"])
    
    with aba_inserir:
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            id_etapa = st.text_input("ID (Ex: A)", max_chars=2, key="id_ins").upper().strip()
        with col2:
            texto_etapa = st.text_input("Texto da Ação:", key="txt_ins")
        with col3:
            tipo_etapa = st.selectbox(
                "Categoria da Ação:", 
                ["Processo Comum (Verde-água)", "Início ou Fim (Azul)", "Decisão / Pergunta (Laranja)", "Sucesso (Verde)", "Erro / Falha (Vermelho)"],
                key="tipo_ins"
            )
        
        proxima_ligacao = st.text_input("Liga ao ID: (Opcional, ex: B)", key="lig_ins").upper().replace(" ", "")

        if st.button("💾 Salvar / Atualizar Etapa", type="primary"):
            if id_etapa and texto_etapa:
                # LÓGICA DE EDIÇÃO: Verifica se o ID já existe na memória
                id_existente = False
                for i, etapa in enumerate(st.session_state.etapas_manuais):
                    if etapa["id"] == id_etapa:
                        # Se já existe, substitui os dados antigos pelos novos (Edição)
                        st.session_state.etapas_manuais[i] = {
                            "id": id_etapa,
                            "texto": texto_etapa,
                            "tipo": tipo_etapa,
                            "proxima": proxima_ligacao
                        }
                        id_existente = True
                        st.success(f"Etapa {id_etapa} editada e atualizada com sucesso!")
                        break
                
                # Se não existir, adiciona normalmente
                if not id_existente:
                    st.session_state.etapas_manuais.append({
                        "id": id_etapa,
                        "texto": texto_etapa,
                        "tipo": tipo_etapa,
                        "proxima": proxima_ligacao
                    })
                    st.success(f"Etapa {id_etapa} criada com sucesso!")
                st.rerun()
            else:
                st.warning("Preencha o ID e o Texto antes de salvar.")

    with aba_remover:
        st.write("Digite o ID da caixa que deseja apagar do fluxo:")
        id_para_remover = st.text_input("ID para remover (Ex: B):", max_chars=2).upper().strip()
        if st.button("🗑️ Apagar esta Etapa"):
            if id_para_remover:
                # Filtra a lista mantendo apenas o que for diferente do ID digitado
                lista_filtrada = [et for et in st.session_state.etapas_manuais if et["id"] != id_para_remover]
                
                if len(lista_filtrada) < len(st.session_state.etapas_manuais):
                    st.session_state.etapas_manuais = lista_filtrada
                    st.success(f"Etapa {id_para_remover} removida com sucesso!")
                    st.rerun()
                else:
                    st.error(f"O ID {id_para_remover} não foi encontrado no fluxo.")

    # Se existirem etapas, monta o gráfico dinamicamente
    if len(st.session_state.etapas_manuais) > 0:
        st.divider()
        colA, colB = st.columns([4, 1])
        with colA:
            st.write("#### 📋 Tabela de Controle de Etapas")
            # Mostra uma tabela simples para o usuário ver os IDs criados atualmente
            st.dataframe(st.session_state.etapas_manuais, use_container_width=True)
        with colB:
            if st.button("💥 Resetar Todo o Fluxo", use_container_width=True):
                st.session_state.etapas_manuais = []
                st.rerun()

        # Montagem do código Mermaid via Python
        codigo_manual = f"{tipo_grafico_mermaid}\n"
        codigo_manual += "classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;\n"
        codigo_manual += "classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;\n"
        codigo_manual += "classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;\n"
        codigo_manual += "classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;\n"
        codigo_manual += "classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;\n"

        for et in st.session_state.etapas_manuais:
            texto_limpo = et["texto"].replace('"', "'")
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
            
            if et["proxima"]:
                ligacoes = et["proxima"].split(",")
                for ligacao in ligacoes:
                    if ligacao:
                        codigo_manual += f'    {et["id"]} --> {ligacao}\n'

        renderizar_mermaid(codigo_manual, orientacao, altura_grafico)
