import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Configuração da página em Modo Largo (Tela Cheia)
st.set_page_config(
    page_title="Gerador de Fluxogramas Pro",
    page_icon="🤖",
    layout="wide"
)

# 2. Conectando a sua chave do Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. Descoberta automática do modelo de IA
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
# 4. BARRA LATERAL (DESIGN PROFISSIONAL)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=80)
    st.title("Configurações Pro")
    st.write("Ajuste o visual do seu gráfico em tempo real.")
    
    st.divider()
    
    orientacao = st.selectbox(
        "Direção do Diagrama:", 
        ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"]
    )
    
    altura_grafico = st.slider(
        "Altura do Painel (Pixels):", 
        min_value=400, 
        max_value=2000, 
        value=600, 
        step=100
    )
    
    st.divider()
    st.info(f"⚡ Sistema operacional rodando com: {modelo_valido}")

# ==========================================
# 5. ÁREA PRINCIPAL DA TELA
# ==========================================
st.title("Gerador de Fluxogramas Automático 🤖")
st.write("Escreva o seu processo abaixo e deixe a IA cuidar do design corporativo.")

tipo_grafico = "graph TD" if "Vertical" in orientacao else "graph LR"
texto_usuario = st.text_area("Digite ou cole o seu processo aqui:", height=150, placeholder="Ex: O cliente faz o pedido, o financeiro aprova...")

if st.button("Gerar Fluxograma Avançado", type="primary"):
    if texto_usuario.strip() == "":
        st.warning("Por favor, digite um processo válido primeiro.")
    else:
        prompt_secreto = f"""
        Você é um designer sênior especialista em diagramas Mermaid.js corporativos.
        Transforme o seguinte texto em um código Mermaid do tipo '{tipo_grafico}'.
        
        REGRAS VITAIS DE DESIGN:
        - Mapeie TODAS as etapas do texto do início ao fim (erros, sucessos e retornos).
        - Use textos curtíssimos dentro dos blocos (máximo 3 palavras por caixa).
        
        Não dê explicações, responda APENAS o código limpo.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Analisando processo e estruturando design gráfico..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                use_max_width = "false" if "Horizontal" in orientacao else "true"
                
                # HTML AVANÇADO: Contém estilos profissionais e a função JavaScript para download
                html_mermaid = f"""
                    <html style="background-color: transparent;">
                    <head>
                        <style>
                            body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: transparent; }}
                            .container {{ position: relative; width: 100%; height: 100%; }}
                            /* Botão de download elegante no estilo SaaS */
                            .btn-download {{
                                position: absolute;
                                top: 10px;
                                right: 10px;
                                background-color: #0288d1;
                                color: white;
                                border: none;
                                padding: 8px 14px;
                                font-size: 13px;
                                font-weight: bold;
                                border-radius: 4px;
                                cursor: pointer;
                                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                                z-index: 9999;
                                transition: background 0.2s;
                            }}
                            .btn-download:hover {{ background-color: #01579b; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <button class="btn-download" onclick="baixarFluxograma()">📥 Baixar Imagem (PNG)</button>
                            
                            <div class="mermaid" id="diagrama_fluxo">
                                {codigo_mermaid}
                            </div>
                        </div>

                        <script type="module">
                            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                            mermaid.initialize({{ 
                                startOnLoad: true, 
                                theme: 'base',
                                flowchart: {{ useMaxWidth: {use_max_width} }},
                                themeVariables: {{
                                    primaryColor: '#f1f8e9',
                                    primaryTextColor: '#2e7d32',
                                    lineColor: '#4caf50',
                                    nodeBorder: '#4caf50'
                                }}
                            }});
                        </script>

                        <script>
                            // Função mágica que converte o gráfico dinâmico em uma foto baixável
                            function baixarFluxograma() {{
                                const svg = document.querySelector('.mermaid svg');
                                if (!svg) {{ alert('Aguarde o gráfico carregar completamente.'); return; }}
                                
                                const svgData = new XMLSerializer().serializeToString(svg);
                                const canvas = document.createElement('canvas');
                                const ctx = canvas.getContext('2d');
                                const img = new Image();
                                
                                // Define tamanho extra para garantir alta resolução ao abrir no Photoshop
                                canvas.width = svg.getBoundingClientRect().width * 2;
                                canvas.height = svg.getBoundingClientRect().height * 2;
                                
                                img.onload = function() {{
                                    ctx.fillStyle = '#ffffff'; // Fundo branco de estúdio
                                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                                    
                                    const a = document.createElement('a');
                                    a.download = 'meu_fluxograma_profissional.png';
                                    a.href = canvas.toDataURL('image/png');
                                    a.click();
                                }};
                                
                                img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
                            }}
                        </script>
                    </body>
                    </html>
                """
                
                # Renderiza a tela limpa integrada
                components.html(html_mermaid, height=altura_grafico, scrolling=True)
                
        except Exception as e:
            st.error(f"Erro ao processar o design: {e}")
