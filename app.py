import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Configuração da página do Streamlit para o modo "Largo" (ocupa melhor a tela)
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
st.write("Descreva o seu processo e a IA criará o gráfico profissional!")

texto_usuario = st.text_area("Descreva o processo aqui:", height=120)

if st.button("Gerar Fluxograma", type="primary"): # Botão azul de destaque
    if texto_usuario.strip() == "":
        st.warning("Por favor, digite um processo na caixa de texto primeiro.")
    else:
        # PROMPT AVANÇADO: Exige um layout limpo, compacto e equilibrado
        prompt_secreto = f"""
        Você é um designer especialista em diagramas Mermaid.js profissionais.
        Transforme o seguinte texto em um código Mermaid do tipo 'graph TD' (de cima para baixo).
        
        DIRETRIZES DE DESIGN:
        - Organize o diagrama de forma muito compacta, simétrica e equilibrada.
        - Não faça uma linha única gigante. Use ramificações bem estruturadas.
        - Mapeie todas as etapas, decisões, caminhos de erro e sucesso do texto.
        - Use textos curtos dentro das caixas (no máximo 3 ou 4 palavras por caixa).
        
        Não dê explicações. Devolva APENAS o código puro do gráfico.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Desenhando o fluxograma..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                # HTML SEAMLESS: Sem bordas, sem fundo diferente, totalmente integrado ao Streamlit
                html_mermaid = f"""
                    <html style="background-color: transparent;">
                    <body style="margin: 0; padding: 0; background-color: transparent; display: flex; justify-content: center;">
                        <script type="module">
                            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                            mermaid.initialize({{ 
                                startOnLoad: true, 
                                theme: 'base',
                                themeVariables: {{
                                    primaryColor: '#e1f5fe',
                                    primaryTextColor: '#01579b',
                                    lineColor: '#0288d1',
                                    nodeBorder: '#0288d1'
                                }}
                            }});
                        </script>
                        <div class="mermaid" style="width: 100%; max-width: 900px;">
                            {codigo_mermaid}
                        </div>
                    </body>
                    </html>
                """
                # Renderiza o componente de forma limpa e com espaço suficiente (height=700)
                components.html(html_mermaid, height=700)
                
        except Exception as e:
            st.error(f"Ocorreu um erro na hora de desenhar: {e}")
