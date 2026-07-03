import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json
import re

st.set_page_config(page_title="Gerador de Fluxos", layout="wide")

if "etapas" not in st.session_state: st.session_state.etapas = []

# Autenticação
if "GROQ_API_KEY" not in st.secrets:
    st.error("Configure a GROQ_API_KEY nos Secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Função de IA Sanitizada
def processar_ia(texto):
    try:
        prompt = f"""Extraia o fluxo de processo para JSON.
        Regras:
        1.IDs devem ser números ou letras simples.
        2. Decisões usam "proxima_sim" e "proxima_nao" com IDs.
        3. Se "acompanhar/verificar", faça o NÃO voltar para o ID da etapa anterior.
        Formato JSON: {{"fluxo": [{{"id": "1", "texto": "Início", "tipo": "Início", "proxima": "2"}}, ...]}}
        Texto: {texto}"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("fluxo", [])
    except: return []

# Limpeza de strings para Mermaid
def safe_id(val): return re.sub(r'[^a-zA-Z0-9]', '_', str(val))
def safe_txt(val): return str(val).replace('"', "'").replace("\n", " ")

st.title("🎨 Gerador de Fluxos Profissional")
texto = st.text_area("Descreva o processo:", height=150)

if st.button("✨ Gerar Fluxo"):
    if texto:
        st.session_state.etapas = processar_ia(texto)
        st.rerun()

st.session_state.etapas = st.data_editor(st.session_state.etapas, num_rows="dynamic", use_container_width=True)

if st.session_state.etapas:
    st.divider()
    
    # Gerador Mermaid Blindado
    codigo = "graph TD\n"
    # Estilos simples para evitar erro
    codigo += "classDef default fill:#f9f9f9,stroke:#333;\n"
    
    for et in st.session_state.etapas:
        i = safe_id(et['id'])
        t = safe_txt(et['texto'])
        ty = et.get('tipo', 'Processo')
        
        if ty == "Decisão": codigo += f'{i}{{"{t}"}}\n'
        else: codigo += f'{i}["{t}"]\n'
        
        prox = str(et.get('proxima', ''))
        if prox:
            for conn in prox.split(","):
                conn = conn.strip()
                if "|" in conn:
                    p = conn.split("|")
                    codigo += f"{i} -->|{p[1]}| {safe_id(p[0])}\n"
                else:
                    codigo += f"{i} --> {safe_id(conn)}\n"

    # Download e Render
    st.download_button("📥 Baixar .mmd", data=codigo, file_name="fluxo.mmd")
    
    components.html(f"""
        <div class="mermaid">{codigo}</div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{startOnLoad:true}});
        </script>
    """, height=600)
