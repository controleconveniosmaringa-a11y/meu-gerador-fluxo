import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Configuração da página com o novo nome limpo e Modo Largo
st.set_page_config(
    page_title="Gerador de Fluxogramas",
    page_icon="📊",
    layout="wide"
)

# 2. Conectando a chave do Gemini
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

# 4. BARRA LATERAL (Configurações visuais discretas)
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

# 5. ÁREA PRINCIPAL (Título atualizado)
st.title("Gerador de Fluxogramas 📊")
st.write("Descreva o seu processo e a IA criará um diagrama profissional, colorido e categorizado.")

tipo_grafico = "graph TD" if "Vertical" in orientacao else "graph LR"
texto_usuario = st.text_area("Descreva o seu processo aqui:", height=150, placeholder="Ex: O cliente solicita o suporte, o técnico analisa o caso...")

if st.button("Gerar Fluxograma Profissional", type="primary"):
    if texto_usuario.strip() == "":
        st.warning("Por favor, insira a descrição de um processo.")
    else:
        # PROMPT AVANÇADO: Força a quebra de texto (<br/>) e a aplicação de cores por contexto
        prompt_secreto = f"""
        Você é um designer especialista em diagramas Mermaid.js corporativos.
        Transforme o texto fornecido em um código Mermaid do tipo '{tipo_grafico}'.
        
        REGRAS CRÍTICAS DE DESIGN E TEXTO (PARA NÃO CORTAR):
        1. QUEBRA DE TEXTO: Para garantir que o texto NÃO fique cortado nas laterais das caixas, você deve quebrar as linhas manualmente usando a tag <br/> se a frase tiver mais de 2 ou 3 palavras. 
           Exemplo ruim: A["Verificar a documentação enviada"]
           Exemplo perfeito para não cortar: A["Verificar a<br/>documentação enviada"]
        
        2. FORMATOS GEOMÉTRICOS:
           - Início/Fim do fluxo: Use cantos arredondados, ex: ID([Texto])
           - Decisões/Perguntas: Use losangos, ex: ID{{Texto}}
           - Sistemas/Bancos de dados: Use cilindros, ex: ID[(Texto)]
           - Etapas normais: Use retângulos, ex: ID[Texto]
        
        3. SISTEMA DE CORES PROFISSIONAL (Adicione estas definições exatas no FINAL do código):
           classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
           classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;
           classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;
           classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;
           classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;
           
           Aplique as classes aos nós de forma lógica no fim do código (Ex: class A processo; class B decisao;):
           - Nós de início ou fim -> classe 'inicio' (Azul)
           - Etapas e ações comuns -> classe 'processo' (Verde-água)
           - Caixas de decisão/perguntas -> classe 'decisao' (Laranja)
           - Resultados de sucesso/conclusão -> classe 'sucesso' (Verde)
           - Caminhos de erro, falhas ou rejeição -> classe 'erro' (Vermelho)
        
        4. ÍCONES (FontAwesome v6):
           Insira ícones nas caixas se fizer sentido com o contexto, ex: "fa:fa-user Cliente", "fa:fa-file Documento", "fa:fa-envelope Email".
        
        Não dê nenhuma explicação ou introdução. Retorne APENAS o código puro do Mermaid.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Estruturando o layout e aplicando paleta de cores..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                use_max_width = "false" if "Horizontal" in orientacao else "true"
                
                # HTML limpo com injeção de fontes modernas e FontAwesome
                html_mermaid = f"""
                    <html>
                    <head>
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
                        <style>
                            body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: transparent; }}
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
                                transition: background 0.2s;
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
                                theme: 'null', /* Desativa o tema padrão para usar nossas classes customizadas */
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
                                    a.download = 'fluxograma_colorido.png';
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
            st.error(f"Erro ao processar o design visual: {e}")
