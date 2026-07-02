import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# Puxando a chave do cofre (Secrets) do Streamlit
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ATUALIZADO: Usando o modelo flash, que é rápido e não dá o erro "Not Found"
modelo = genai.GenerativeModel('gemini-1.5-flash')

st.title("Gerador de Fluxogramas Automático 🤖")
st.write("Descreva o seu processo e a IA criará o gráfico profissional!")

# Caixa onde o usuário digita o texto normal
texto_usuario = st.text_area("Descreva o processo aqui:", height=150)

if st.button("Gerar Fluxograma"):
    
    # Instrução secreta que passamos para a IA
    prompt_secreto = f"""
    Você é um especialista em criar diagramas Mermaid.js.
    Transforme o seguinte texto em um código Mermaid do tipo 'graph TD'.
    Não me dê explicações, me devolva APENAS o código do gráfico. Se houver etapas de sucesso ou erro, use cores discretas nas caixas.
    Texto do usuário: {texto_usuario}
    """
    
    # A IA gera o código do gráfico
    resposta_ia = modelo.generate_content(prompt_secreto)
    
    # Limpando a resposta caso a IA mande aspas ou marcações de código
    codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
    
    # O Site desenha o gráfico profissional
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
