import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json

# ==========================================
# 1. CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Gerador de Fluxos (Miro Clone)", page_icon="🎨", layout="wide")

if "etapas" not in st.session_state: 
    st.session_state.etapas = []

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("⚠️ Configure sua GROQ_API_KEY no painel de Secrets do Streamlit.")
    st.stop()

# ==========================================
# 2. MOTOR DE DESIGN (ESTÉTICA MIRO + ZOOM)
# ==========================================
def renderizar_mermaid(codigo_mermaid, scale, altura=900):
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
            /* Container ajustável pelo Zoom */
            #graph-container {{ 
                display: flex; 
                justify-content: center; 
                transform: scale({scale}); 
                transform-origin: top center; 
                transition: transform 0.2s;
            }}
        </style>
    </head>
    <body>
        <div id="graph-container" class="mermaid">{codigo_mermaid}</div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'base',
                themeVariables: {{ 
                    fontFamily: 'Arial, sans-serif', fontSize: '14px', 
                    lineColor: '#94a3b8', lineWidth: '2px', 
                    clusterBkg: 'transparent', clusterBorder: '#cbd5e1' 
                }},
                themeCSS: `
                    .node rect, .node circle, .node polygon, .node path {{ filter: drop-shadow(0 2px 5px rgba(0,0,0,0.06)); }}
                    .node label {{ padding: 10px !important; }} 
                    .edgeLabel {{ background-color: #f4f5f9 !important; padding: 2px 8px !important; font-weight: normal; color: #475569; }}
                `,
                flowchart: {{ useMaxWidth: false, curve: 'basis', nodeSpacing: 60, rankSpacing: 90 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Arquiteto BPMN. Extraia o fluxo para JSON.
    Regras:
    1. Início e Fim obrigatórios. 
    2. Decisões usam "proxima_sim" e "proxima_nao".
    3. Sistemas = Documento.
    4. Loops: Se "acompanhar", crie um loop voltando para a etapa anterior no NÃO.
    
    Retorne JSON com chave "fluxo".
    Texto: {texto}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"} 
        )
        dados = json.loads(completion.choices[0].message.content)
        fluxo = dados.get("fluxo", [])
        
        for etapa in fluxo:
            if etapa.get("tipo") == "Decisão":
                sim = etapa.pop("proxima_sim", "")
                nao = etapa.pop("proxima_nao", "")
                if sim and nao: etapa["proxima"] = f"{sim}|SIM, {nao}|NÃO"
                elif sim: etapa["proxima"] = f"{sim}|SIM"
                elif nao: etapa["proxima"] = f"{nao}|NÃO"
        return fluxo
    except: return []

# ==========================================
# 4. INTERFACE
# ==========================================
st.title("🎨 Gerador de Fluxos (Clone do Miro)")

# --- Controle de Zoom ---
zoom_level = st.slider("Ajustar Zoom do Fluxograma", 0.5, 2.0, 1.0, 0.1)

orientacao = st.radio("Orientação:", ["Horizontal", "Vertical"], horizontal=True, index=1)
st.session_state.etapas = st.data_editor(st.session_state.etapas, num_rows="dynamic", use_container_width=True)

if st.button("✨ Gerar/Atualizar Fluxo"):
    if st.session_state.etapas:
        st.rerun()

# ==========================================
# 5. GERADOR E RENDERIZAÇÃO
# ==========================================
if len(st.session_state.etapas) > 0:
    st.divider()
    
    # Blindagem Anti-Blocos Soltos
    id_fim = next((str(e["id"]) for e in st.session_state.etapas if e["tipo"] == "Fim"), "999")
    for et in st.session_state.etapas:
        if et["tipo"] != "Fim" and not str(et.get("proxima", "")).strip():
            et["proxima"] = id_fim

    codigo = "graph TD\n" if "Vertical" in orientacao else "graph LR\n"
    codigo += "classDef Início fill:#a7f3d0,stroke:#059669,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Processo fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#1e293b,rx:8px,ry:8px;\n"
    codigo += "classDef Decisão fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Documento fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Fim fill:#a7f3d0,stroke:#059669,stroke-width:2px,color:#1e293b;\n\n"
    
    for et in st.session_state.etapas:
        i, t, ty, p = str(et['id']), str(et['texto']), et.get('tipo', 'Processo'), str(et.get('proxima', ''))
        if ty == "Decisão": codigo += f'{i}{{"{t}"}}:::Decisão\n'
        elif ty == "Início": codigo += f'{i}(["{t}"]):::Início\n'
        elif ty == "Fim": codigo += f'{i}(["{t}"]):::Fim\n'
        elif ty == "Documento": codigo += f'{i}[/"{t}"/]:::Documento\n'
        else: codigo += f'{i}["{t}"]:::Processo\n'
        
        if p:
            for conn in p.split(","):
                conn = conn.strip()
                if "|" in conn:
                    partes = conn.split("|")
                    codigo += f"{i} -->|{partes[1]}| {partes[0].replace(' ', '_')}\n"
                else:
                    codigo += f"{i} --> {conn.replace(' ', '_')}\n"
    
    col1, col2 = st.columns([8, 2])
    with col2:
        st.download_button("📥 Baixar .mmd", data=codigo, file_name="fluxo.mmd")
    
    renderizar_mermaid(codigo, scale=zoom_level)
