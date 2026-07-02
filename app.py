import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Conectando a chave secreta
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. AUTO-DESCOBERTA DO MODELO (O segredo para resolver o erro 404)
# O código pergunta ao Google qual modelo está disponível para a sua chave
modelo_disponivel = 'gemini-pro' # Fallback de segurança
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            modelo_disponivel = m.name
            if 'flash' in m.name.lower(): 
                break # Se achar o modelo Flash (mais rápido), escolhe ele e para de procurar
except:
    pass

modelo = genai.GenerativeModel(modelo_disponivel)

# 3. Construção da Tela
st.title("Gerador de Fluxogramas Automático 🤖")
st.write("Descreva o seu processo e a IA criará o gráfico profissional!")

texto_usuario = st.text_area("Descreva o processo aqui:", height=150)

if st.button("Gerar Fluxograma"):
    # Se a pessoa clicar no botão sem digitar nada, avisamos ela
    if texto_usuario.strip() == "":
        st.warning("Por favor, digite um processo na caixa de texto primeiro.")
    else:
        prompt_secreto = f"""
        Você é um especialista em criar diagramas Mermaid.js.
        Transforme o seguinte texto em um código Mermaid do tipo 'graph TD'.
        Não me dê explicações, me devolva APENAS o código do gráfico. Se houver etapas de sucesso ou erro, use cores discretas nas caixas.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            # Mostra um aviso de carregamento enquanto a IA pensa
            with st.spinner("Desenhando o fluxograma..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                html_mermaid = f"""
                    <script type="module">
                        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                        mermaid.initialize({{ startOnLoad: true, theme: 'base' }});
                    </script>
                    <div class="mermaid">
                        {codigo_mermaid}
                    </div>
                """
                components.html(html_mermaid, height=600)
        except Exception as e:
            # Se der qualquer erro, mostra na tela de forma amigável
            st.error(f"Ocorreu um erro de comunicação com a IA: {e}")
