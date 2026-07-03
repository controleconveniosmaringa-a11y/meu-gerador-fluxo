import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json

# ==========================================
# 1. CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Gerador de Fluxos", page_icon="🎨", layout="wide")

if "etapas" not in st.session_state: 
    st.session_state.etapas = []

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("⚠️ Configure sua GROQ_API_KEY no painel de Secrets do Streamlit.")
    st.stop()

# ==========================================
# 2. MOTOR DE DESIGN (ESTÉTICA MIRO - TAMANHO EQUILIBRADO)
# ==========================================
def renderizar_mermaid(codigo_mermaid, scale, orientacao, altura=900):
    # CSS dinâmico baseado na orientação
    max_height = "1000px" if orientacao == "Vertical" else "none"
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
            .mermaid-wrapper {{ 
                display: flex; justify-content: center; overflow: auto; 
                max-height: {max_height}; width: 100%;
            }}
            #graph-container {{ 
                transform: scale({scale}); 
                transform-origin: top center; 
                transition: transform 0.2s;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid-wrapper">
            <div id="graph-container" class="mermaid">{codigo_mermaid}</div>
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true, theme: 'base',
                themeVariables: {{ fontFamily: 'Arial', fontSize: '16px', lineColor: '#94a3b8', lineWidth: '2px' }},
                flowchart: {{ useMaxWidth: false, curve: 'basis', nodeSpacing: 80, rankSpacing: 100 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (BLINDADA)
# ==========================================
def processar_ia(texto):
    prompt = f"""Extraia o fluxo de processo para JSON.
    Regras: Início e Fim obrigatórios. Decisões têm "proxima_sim" e "proxima_nao".
    Se "acompanhar/verificar", o NÃO volta para o ID anterior.
    Retorne apenas JSON: {{"fluxo": [{{"id": "1", "texto": "Início", "tipo": "Início", "proxima": "2"}}, ...]}}
    Texto: {texto}"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        fluxo = data.get("fluxo", [])
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

# ==========================================
# 4. INTERFACE
# ==========================================
st.title("🎨 Gerador de Fluxos")

col1, col2 = st.columns([2, 1])
with col1:
    texto_processo = st.text_area("Descreva o processo:", height=150)
    if st.button("✨ Gerar Fluxograma"):
        if texto_processo.strip():
            st.session_state.etapas = processar_ia(texto_processo)
            st.rerun()

with col2:
    zoom = st.slider("Ajustar Zoom", 0.5, 2.0, 1.0, 0.1)
    orientacao = st.radio("Direção", ["Horizontal", "Vertical"], horizontal=True, index=1)

st.session_state.etapas = st.data_editor(st.session_state.etapas, num_rows="dynamic", use_container_width=True)

# ==========================================
# 5. GERADOR E RENDERIZAÇÃO
# ==========================================
if st.session_state.etapas:
    st.divider()
    id_fim = next((str(e["id"]) for e in st.session_state.etapas if e["tipo"] == "Fim"), "999")
    for et in st.session_state.etapas:
        if et["tipo"] != "Fim" and not str(et.get("proxima", "")).strip():
            et["proxima"] = id_fim

    codigo = "graph TD\n" if orientacao == "Vertical" else "graph LR\n"
    codigo += "classDef default fill:#f9f9f9,stroke:#333; classDef Decisão fill:#bfdbfe,stroke:#2563eb;\n"
    
    for et in st.session_state.etapas:
        i, t, ty = str(et['id']).replace(' ','_'), str(et['texto']).replace('"', "'"), et.get('tipo', 'Processo')
        if ty == "Decisão": codigo += f'{i}{{"{t}"}}:::Decisão\n'
        else: codigo += f'{i}["{t}"]\n'
        
        if et.get('proxima'):
            for conn in str(et['proxima']).split(","):
                conn = conn.strip()
                if "|" in conn:
                    p = conn.split("|")
                    codigo += f"{i} -->|{p[1]}| {p[0].replace(' ', '_')}\n"
                else:
                    codigo += f"{i} --> {conn.replace(' ', '_')}\n"

    st.download_button("📥 Baixar .mmd", data=codigo, file_name="fluxo.mmd")
    renderizar_mermaid(codigo, zoom, orientacao)
