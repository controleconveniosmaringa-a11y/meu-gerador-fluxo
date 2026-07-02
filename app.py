import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Configuração da página para usar a tela cheia (Modo Largo)
st.set_page_config(layout="wide")

# 2. Conectando a sua chave
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

# 4. Interface do Usuário
st.title("Gerador de Fluxogramas Automático 🤖")
st.write("Descreva o seu processo e ajuste o visual do gráfico como preferir!")

# PAINEL DE CONTROLE (Deixa o site super profissional)
st.write("### 🛠️ Configurações do Gráfico")
col1, col2 = st.columns(2)

with col1:
    orientacao = st.selectbox(
        "Direção do Fluxograma:", 
        ["Cima para Baixo (Vertical)", "Esquerda para Direita (Horizontal)"]
    )

with col2:
    altura_grafico = st.slider(
        "Altura da área do gráfico (Aumente se o fluxo cortar!):", 
        min_value=400, 
        max_value=2000, 
        value=800, 
        step=100
    )

# Mapeia a escolha do usuário para o código que a IA vai usar
tipo_grafico = "graph TD" if "Vertical" in orientacao else "graph LR"

# Caixa de texto
texto_usuario = st.text_area("Descreva o processo aqui:", height=120)

if st.button("Gerar Fluxograma", type="primary"):
    if texto_usuario.strip() == "":
        st.warning("Por favor, digite um processo na caixa de texto primeiro.")
    else:
        prompt_secreto = f"""
        Você é um designer especialista em diagramas Mermaid.js profissionais.
        Transforme o seguinte texto em um código Mermaid do tipo '{tipo_grafico}'.
        
        DIRETRIZES DE DESIGN:
        - Organize o diagrama de forma limpa, compacta e equilibrada.
        - Mapeie todas as etapas, decisões, caminhos de erro e sucesso do texto. Não pule nada.
        - Use textos curtos dentro das caixas (no máximo 3 ou 4 palavras por caixa).
        
        Não dê explicações. Devolva APENAS o código puro do gráfico.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Desenhando o fluxograma..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                # Se for horizontal, desativamos o max-width para não espremer as letras
                use_max_width = "false" if "Horizontal" in orientacao else "true"
                
                # HTML limpo e responsivo com rolagem suave se passar do tamanho escolhido
                html_mermaid = f"""
                    <html style="background-color: transparent;">
                    <body style="margin: 0; padding: 10px; background-color: transparent;">
                        <script type="module">
                            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                            mermaid.initialize({{ 
                                startOnLoad: true, 
                                theme: 'base',
                                flowchart: {{ useMaxWidth: {use_max_width} }},
                                themeVariables: {{
                                    primaryColor: '#e1f5fe',
                                    primaryTextColor: '#01579b',
                                    lineColor: '#0288d1',
                                    nodeBorder: '#0288d1'
                                }}
                            }});
                        </script>
                        <div class="mermaid">
                            {codigo_mermaid}
                        </div>
                    </body>
                    </html>
                """
                # Usa a altura dinâmica vinda do Slider do Streamlit
                components.html(html_mermaid, height=altura_grafico, scrolling=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro na hora de desenhar: {e}")
