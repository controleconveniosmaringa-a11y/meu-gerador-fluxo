import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json

# Configuração da página
st.set_page_config(page_title="Miro Clone", layout="wide")

# Inicialização
if "etapas" not in st.session_state: st.session_state.etapas = []

# Autenticação
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Configure sua GROQ_API_KEY nos Secrets.")
    st.stop()

# Função IA com tratamento de erros
def processar_ia(texto):
    try:
        prompt = f"""Extraia o fluxo de processo deste texto para JSON.
        Regras: 
        1. Início e Fim obrigatórios. 
        2. Decisões têm "proxima_sim" e "proxima_nao". 
        3. Sistemas (SEI/Oxy) = Documento.
        4. O 'Fim' deve ter a proxima: "".
        Formato JSON: {{"fluxo": [{{"id": "1", "texto": "Início", "tipo": "Início", "proxima": "2"}}, ...]}}
        Texto: {texto}"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        fluxo = data.get("fluxo", [])
        
        # Limpeza de None e formatação de setas
        for et in fluxo:
            for k, v in et.items():
                if v is None: et[k] = ""
            if et.get("tipo") == "Decisão":
                s = et.pop("proxima_sim", "")
                n = et.pop("proxima_nao", "")
                if s and n: et["proxima"] = f"{s}|SIM, {n}|NÃO"
                elif s: et["proxima"] = f"{s}|SIM"
                elif n: et["proxima"] = f"{n}|NÃO"
        return fluxo
    except: return []

# --- INTERFACE ---
st.title("🎨 Gerador de Fluxos")

# Input sempre visível
texto_processo = st.text_area("Descreva o seu processo aqui:", height=150)

if st.button("✨ Gerar Fluxo"):
    if texto_processo.strip():
        st.session_state.etapas = processar_ia(texto_processo)
        st.rerun()

# Edição
st.session_state.etapas = st.data_editor(st.session_state.etapas, num_rows="dynamic", use_container_width=True)

# Renderização
if st.session_state.etapas:
    st.divider()
    # Blindagem de Blocos Soltos
    id_fim = next((str(e["id"]) for e in st.session_state.etapas if e["tipo"] == "Fim"), "999")
    for et in st.session_state.etapas:
        if et["tipo"] != "Fim" and not str(et.get("proxima", "")).strip():
            et["proxima"] = id_fim

    # Código Mermaid
    codigo = "graph TD\n"
    codigo += "classDef Início fill:#a7f3d0,stroke:#059669; classDef Processo fill:#fef08a,stroke:#ca8a04; classDef Decisão fill:#bfdbfe,stroke:#2563eb; classDef Documento fill:#fef08a,stroke:#ca8a04; classDef Fim fill:#a7f3d0,stroke:#059669;\n"
    
    for et in st.session_state.etapas:
        i, t, ty = str(et['id']), str(et['texto']), et.get('tipo', 'Processo')
        if ty == "Decisão": codigo += f'{i}{{"{t}"}}:::{ty}\n'
        else: codigo += f'{i}["{t}"]:::{ty}\n'
        
        if et.get('proxima'):
            for conn in str(et['proxima']).split(","):
                conn = conn.strip()
                if "|" in conn:
                    p = conn.split("|")
                    codigo += f"{i} -->|{p[1]}| {p[0].replace(' ', '_')}\n"
                else:
                    codigo += f"{i} --> {conn.replace(' ', '_')}\n"

    # Download e Exibição
    st.download_button("📥 Baixar Fluxo (.mmd)", data=codigo, file_name="fluxo.mmd")
    components.html(f"""
        <div class="mermaid">{codigo}</div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
    """, height=600)
