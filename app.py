import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Configuração da página
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
        value=800, 
        step=100
    )

# 5. ÁREA PRINCIPAL
st.title("Gerador de Fluxogramas 📊")
st.write("Descreva o seu processo e a IA criará um diagrama profissional, colorido e sem cortes.")

tipo_grafico = "graph TD" if "Vertical" in orientacao else "graph LR"
texto_usuario = st.text_area("Descreva o seu processo aqui:", height=150, placeholder="Ex: O cliente solicita o suporte...")

if st.button("Gerar Fluxograma Profissional", type="primary"):
    if texto_usuario.strip() == "":
        st.warning("Por favor, insira a descrição de um processo.")
    else:
        # PROMPT BLINDADO: Força o uso de IDs simples (A, B, C) para evitar o Syntax Error
        prompt_secreto = f"""
        Você é um gerador estrito de código Mermaid.js funcional, sem erros de sintaxe.
        Transforme o texto fornecido em um diagrama válido do tipo '{tipo_grafico}'.
        
        REGRAS DE SINTAXE OBRIGATÓRIAS (PARA EVITAR SYNTAX ERROR):
        1. IDENTIFICADORES DOS NÓS: Use APENAS letras simples sequenciais como IDs das caixas (A, B, C, D, E, F, G, etc.). Nunca use palavras do texto ou espaços como IDs.
        2. TEXTOS COM ASPAS: Todo texto descritivo dentro das caixas DEVE estar entre aspas duplas, ex: A["Texto"].
        3. QUEBRA DE LINHA INTERNA: Para o texto não cortar, insira a tag <br/> a cada duas ou três palavras dentro das aspas. Exemplo: A["Verificar o<br/>saldo bancário"].
        
        FORMATOS E ESTILOS COMPATÍVEIS (Injete a classe no próprio nó para evitar falhas):
        - Início ou Fim do fluxo: Use formato arredondado e classe inicio. Ex: A(["fa:fa-play Início"]):::inicio
        - Etapas/Ações comuns: Use retângulo e classe processo. Ex: B["fa:fa-gear Ação"]:::processo
        - Decisões/Perguntas: Use losango e classe decisao. Ex: C{{"fa:fa-question Pergunta?"}}:::decisao
        - Resultados de Sucesso: Use formato arredondado e classe sucesso. Ex: D(["fa:fa-check Sucesso"]):::sucesso
        - Erros ou Falhas: Use formato arredondado e classe erro. Ex: E(["fa:fa-triangle-exclamation Falha"]):::erro
        - Servidores/Bancos de Dados: Use cilindro e classe processo. Ex: F[("fa:fa-database Servidor")]:::processo
        
        DEFINIÇÃO DAS CLASSES DE ESTILO (Coloque exatamente estas linhas no final do código):
        classDef inicio fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
        classDef processo fill:#e0f2f1,stroke:#009688,stroke-width:2px,color:#004d40;
        classDef decisao fill:#fff3e0,stroke:#ff9800,stroke-width:2px,color:#e65100;
        classDef sucesso fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;
        classDef erro fill:#ffebee,stroke:#f44336,stroke-width:2px,color:#b71c1c;
        
        Não dê explicações ou introduções. Retorne APENAS o código limpo do Mermaid.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Estruturando o layout e aplicando paleta de cores..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                
                # Limpeza cirúrgica do texto para extrair apenas o código válido
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                # Exibe uma ferramenta de inspecionar código para ajudar no desenvolvimento
                with st.expander("⚙️ Verificar Código Gerado (Debug / Photoshop)"):
                    st.code(codigo_mermaid, language="mermaid")
                
                use_max_width = "false" if "Horizontal" in orientacao else "true"
                
                # HTML robusto integrado
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
                components.html(html_mermaid, height=altura_grafico, scrolling=True)
                
        except Exception as e:
            st.error(f"Erro ao processar o design visual: {e}")
