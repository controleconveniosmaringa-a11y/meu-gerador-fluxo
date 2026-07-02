import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Configuração da página em Modo Largo
st.set_page_config(
    page_title="Gerador de Fluxogramas Pro",
    page_icon="🎨",
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

# 4. BARRA LATERAL (Configurações)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208723.png", width=80)
    st.title("Design do Gráfico")
    st.write("Personalize o comportamento do layout.")
    
    st.divider()
    
    orientacao = st.selectbox(
        "Direção do Diagrama:", 
        ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"]
    )
    
    altura_grafico = st.slider(
        "Altura do Painel (Pixels):", 
        min_value=400, 
        max_value=2000, 
        value=700, 
        step=100
    )

# 5. ÁREA PRINCIPAL
st.title("Gerador de Fluxogramas Inteligente com Ícones 🚀")
st.write("A IA agora vai aplicar formatos profissionais e ícones contextuais para cada etapa do seu processo.")

tipo_grafico = "graph TD" if "Vertical" in orientacao else "graph LR"
texto_usuario = st.text_area("Descreva o seu processo:", height=150, placeholder="Ex: O cliente solicita o documento, o sistema gera o arquivo e envia por e-mail...")

if st.button("Gerar Fluxograma Infográfico", type="primary"):
    if texto_usuario.strip() == "":
        st.warning("Por favor, digite um processo válido.")
    else:
        # PROMPT ULTRA DETALHADO: Ensina a IA a usar formas geométricas e ícones do FontAwesome
        prompt_secreto = f"""
        Você é um designer gráfico especialista em diagramas Mermaid.js e arquitetura de processos.
        Transforme o texto fornecido em um código Mermaid do tipo '{tipo_grafico}'.
        
        Siga RIGOROSAMENTE as seguintes instruções de estética profissional:
        
        1. FORMATOS DAS CAIXAS (Use a sintaxe correta do Mermaid):
           - Início/Fim do fluxo: Use bordas arredondadas, ex: ID([Texto])
           - Decisões/Perguntas: Use losangos, ex: ID{{Texto}}
           - Bancos de dados, Servidores ou Sistemas: Use cilindros, ex: ID[(Texto)]
           - Processos normais: Use retângulos comuns, ex: ID[Texto]
        
        2. USO DE ÍCONES (FontAwesome v6):
           Insira ícones relevantes antes do texto dentro das aspas de cada bloco usando a sintaxe 'fa:fa-nome-do-icone'. Exemplos obrigatórios por contexto:
           - Pessoas/Clientes/Atores: Use "fa:fa-user Texto" ou "fa:fa-users Texto"
           - Documentos/Contratos/Relatórios/Arquivos: Use "fa:fa-file-lines Texto" ou "fa:fa-file-pdf Texto"
           - E-mails/Notificações/Mensagens: Use "fa:fa-envelope Texto" ou "fa:fa-bell Texto"
           - Dinheiro/Pagamento/Faturamento: Use "fa:fa-credit-card Texto" ou "fa:fa-dollar-sign Texto"
           - Sucesso/Confirmação: Use "fa:fa-check Texto"
           - Erros/Alertas/Rejeições: Use "fa:fa-triangle-exclamation Texto"
           - Engrenagem/Processamento técnico: Use "fa:fa-gear Texto"
        
        3. REGRAS GERAIS:
           - O texto dentro das caixas deve ser curto (máximo 3 palavras junto com o ícone).
           - Mapeie o texto INTEIRO, incluindo desvios de erro e retornos.
           - Importante: Use aspas duplas internas para os textos com ícones, ex: A(["fa:fa-user Cliente"])
        
        Não dê nenhuma explicação ou introdução. Retorne APENAS o código puro do Mermaid.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Criando formas e injetando ícones profissionais..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                use_max_width = "false" if "Horizontal" in orientacao else "true"
                
                # HTML ATUALIZADO: Carrega o FontAwesome para os ícones aparecerem de verdade
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
                                background-color: #2e7d32;
                                color: white;
                                border: none;
                                padding: 8px 14px;
                                font-size: 13px;
                                font-weight: bold;
                                border-radius: 4px;
                                cursor: pointer;
                                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                                z-index: 9999;
                            }}
                            .btn-download:hover {{ background-color: #1b5e20; }}
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
                                theme: 'base',
                                flowchart: {{ useMaxWidth: {use_max_width} }},
                                themeVariables: {{
                                    primaryColor: '#f5f5f5',
                                    primaryTextColor: '#212121',
                                    lineColor: '#757575',
                                    nodeBorder: '#9e9e9e'
                                }}
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
                                    a.download = 'fluxograma_com_icones.png';
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
            st.error(f"Erro ao processar o design: {e}")
