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
        # PROMPT REFORÇADO: Exige o fluxo COMPLETO e muda para 'graph LR' (Esquerda para Direita)
        prompt_secreto = f"""
        Você é um especialista em criar diagramas Mermaid.js profissionais.
        Transforme o seguinte texto em um código Mermaid do tipo 'graph LR' (da esquerda para a direita).
        
        ATENÇÃO CRÍTICA: Você deve ler o texto ATÉ O FINAL. Mapeie absolutamente todas as etapas mencionadas, incluindo as bifurcações de erro, loops de retorno e telas de sucesso. Não resuma e não pare na metade.
        
        Não me dê explicações, me devolva APENAS o código puro do gráfico dentro da estrutura do Mermaid.
        Texto do usuário: {texto_usuario}
        """
        
        try:
            with st.spinner("Desenhando o fluxograma completo..."):
                resposta_ia = modelo.generate_content(prompt_secreto)
                codigo_mermaid = resposta_ia.text.replace("```mermaid", "").replace("```", "").strip()
                
                # Configuração visual com rolagem ativada (scrolling=True)
                html_mermaid = f"""
                    <div style="overflow: auto; width: 100%; height: 100%;">
                        <script type="module">
                            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                            mermaid.initialize({{ startOnLoad: true, theme: 'base' }});
                        </script>
                        <div class="mermaid">
                            {codigo_mermaid}
                        </div>
                    </div>
                """
                # Adicionado scrolling=True para permitir navegar pelo gráfico se ele crescer
                components.html(html_mermaid, height=600, scrolling=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro na hora de desenhar: {e}")
