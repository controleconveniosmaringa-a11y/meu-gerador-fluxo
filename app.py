import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Configuração da página
st.set_page_config(
    page_title="Gerador de Fluxogramas",
    page_icon="📊",
    layout="wide"
)

# 2. Conectando a chave
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. Descoberta automática do modelo
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

# --- A MÁGICA DO PLANO GRATUITO: MEMÓRIA CACHE ---
# Guarda o resultado por 1 hora (3600 segundos) para não gastar o limite da API
@st.cache_data(ttl=3600, show_spinner=False)
def gerar_grafico_ia(prompt):
    resposta = modelo.generate_content(prompt)
    return resposta.text.replace("```mermaid", "").replace("```", "").strip()
# --------------------------------------------------

# 4. BARRA LATERAL
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=70)
    st.title("Configurações")
    st.write("Ajuste a estrutura do seu gráfico.")
    
    st.divider()
    
    orientacao = st.selectbox(
        "Direção do Layout:", 
        ["Esquerda para Direita (Horizontal)", "Cima para Baixo (Vertical)"]
    )
    
    altura_grafico = st.slider(
        "Altura da Tela (Pixels):", 
        min_value=400, 
        max_value=2000, 
        value=700, 
        step=100
    )

# 5. ÁREA PRINCIPAL
st.title("Gerador de Fluxogramas 📊")
st.write("Versão Otimizada (Free Tier): Sistema inteligente que poupa a cota de requisições.")

tipo_grafico = "graph TD" if "Vertical" in orientacao else "graph LR"
texto_usuario = st.text_area("Descreva o seu processo aqui:", height=150, placeholder="Ex: O analista recebe a solicitação...")

if st.button("Gerar Fluxograma Profissional", type="primary"):
    if texto_usuario.strip() == "":
        st.warning("Por favor, insira a descrição de um processo.")
    else:
        prompt_secreto = f"""
        Você é um gerador estrito de código Mermaid.js funcional, sem erros de sintaxe.
        Transforme o texto fornecido em um diagrama válido do tipo '{tipo_grafico}'.
        
        REGRAS DE SINTAXE OBRIGATÓRIAS (ANTI-ERRO):
        1. IDENTIFICADORES DOS NÓS: Use APENAS letras simples sequenciais como IDs.
        2. TEXTOS COM ASPAS: Todo texto descritivo dentro das caixas DEVE estar entre aspas duplas, ex: A["Texto"].
        3. PROIBIÇÃO DE PARÊNTESES NO TEXTO: Remova ou substitua parênteses brutos por hífens.
        4. QUEBRA DE LINHA: Insira <br/> a cada duas ou três palavras dentro das aspas.
        
        FORMATOS E ESTILOS COMPATÍVEIS:
        - Início/Fim: ID([Texto]):::inicio
        - Etapas: ID[Texto]:::processo
        - Decisões: ID{{Texto}}:::decisao
        - Sucesso: ID([Texto]):::sucesso
        - Erros: ID([Texto]):::erro
        
        DEFINIÇÃO DAS CLASSES:
        classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
        classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;
        classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;
        classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;
        classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;
        
        Não dê explicações. Retorne APENAS o código puro do Mermaid.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Analisando dados e estruturando o fluxo..."):
                # Chama a função com Cache
                codigo_mermaid = gerar_grafico_ia(prompt_secreto)
                
                with st.expander("⚙️ Verificar Código Gerado (Debug)"):
                    st.code(codigo_mermaid, language="mermaid")
                
                use_max_width = "false" if "Horizontal" in orientacao else "true"
                
                html_mermaid = f"""
                    <html>
                    <head>
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
                        <style>
                            body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: transparent; }}
                            .container {{ position: relative; width: 100%; height: 100%; }}
                            .btn-download {{
                                position: absolute;
                                top: 10px;
                                right: 10px;
                                background-color: #1a237e;
                                color: white;
                                border: none;
                                padding: 9px 16px;
                                font-size: 13px;
                                font-weight: bold;
                                border-radius: 4px;
                                cursor: pointer;
                                box-shadow: 0 2px 5px rgba(0,0,0,0.15);
                                z-index: 9999;
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
                                if (!svg) {{ alert('Aguarde o gráfico carregar completamente.'); return; }}
                                
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
                                    a.download = 'fluxograma_processo.png';
                                    a.href = canvas.toDataURL('image/png');
                                    a.click();
                                }};
                                
                                img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
                            }}
                        </script>
                    </body>
                    </html>
                """
                components.html(html_mermaid, height=altura_grafico, scrolling=True)
                
        except Exception as e:
            erro_str = str(e)
            if "429" in erro_str or "quota" in erro_str.lower():
                st.warning("⏳ O limite de segurança do plano gratuito foi atingido. Por favor, aguarde **1 minuto** e tente gerar novamente!")
            else:
                st.error(f"Erro ao processar o design: {e}")
