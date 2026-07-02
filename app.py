import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. Conectando a sua chave NOVA
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. Descoberta automática do modelo
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

# 3. Construção da Tela
st.title("Gerador de Fluxogramas Automático 🤖")
st.write("Descreva o seu processo e a IA criará o gráfico profissional!")

st.success(f"Conectado com sucesso! Usando a inteligência: {modelo_valido}")

texto_usuario = st.text_area("Descreva o processo aqui:", height=150)

if st.button("Gerar Fluxograma"):
    if texto_usuario.strip() == "":
        st.warning("Por favor, digite um processo na caixa de texto primeiro.")
    else:
        prompt_secreto = f"""
        Você é um especialista em criar diagramas Mermaid.js profissionais.
        Transforme o seguinte texto em um código Mermaid do tipo 'graph LR' (da esquerda para a direita).
        
        ATENÇÃO: Mapeie todas as etapas mencionadas, incluindo as bifurcações de erro, loops de retorno e telas de sucesso. Não pare na metade.
        
        Não me dê explicações, me devolva APENAS o código puro do gráfico.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Desenhando o fluxograma completo..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                # CORREÇÃO CRÍTICA: flowchart: {{ useMaxWidth: false }} impede que o gráfico encolha
                html_mermaid = f"""
                    <div style="overflow: auto; width: 100%; height: 550px; padding: 10px; border: 1px solid #eeeeee; border-radius: 5px;">
                        <script type="module">
                            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                            mermaid.initialize({{ 
                                startOnLoad: true, 
                                theme: 'base',
                                flowchart: {{ useMaxWidth: false }} 
                            }});
                        </script>
                        <div class="mermaid">
                            {codigo_mermaid}
                        </div>
                    </div>
                """
                components.html(html_mermaid, height=600, scrolling=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro na hora de desenhar: {e}")
