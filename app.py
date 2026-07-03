import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json
import re

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
# 2. FUNÇÕES DE LIMPEZA (BLINDAGEM MERMAID)
# ==========================================
def sanitize_mermaid_id(id_val):
    # IDs do Mermaid não podem ter espaços ou caracteres especiais
    return re.sub(r'[^a-zA-Z0-9]', '_', str(id_val))

def sanitize_mermaid_text(text_val):
    # Remove aspas duplas que quebram o código
    return str(text_val).replace('"', "'").replace("\n", " ")

# ==========================================
# 3. MOTOR DE DESIGN (ESTÉTICA MIRO)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=1200):
    html = f"""
    <html>
    <body>
        <div class="mermaid">{codigo_mermaid}</div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'base',
                themeVariables: {{ 
                    fontFamily: 'Arial, sans-serif', 
                    fontSize: '16px', 
                    lineColor: '#94a3b8',
                    lineWidth: '2px'
                }},
                flowchart: {{ useMaxWidth: false, htmlLabels: true, curve: 'basis' }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 4. IA (JSON ESTRITO)
# ==========================================
def processar_ia(texto):
    prompt = f"""Extraia o fluxo de processo para JSON.
    Regras:
    1. INÍCIO E FIM OBRIGATÓRIOS.
    2. Decisões usam "proxima_sim" e "proxima_nao".
    3. Retorne apenas JSON com chave "fluxo".
    Texto do usuário: {texto}"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"} 
        )
        dados = json.loads(completion.choices[0].message.content)
        return dados.get("fluxo", [])
    except: return []

# ==========================================
# 5. INTERFACE
# ==========================================
st.title("🎨 Gerador de Fluxos")

orientacao = st.radio("Orientação:", ["Horizontal", "Vertical"], horizontal=True, index=1)
texto = st.text_area("Cole o texto do processo:", height=150)

if st.button("✨ Gerar"):
    if texto.strip():
        st.session_state.etapas = processar_ia(texto)
        st.rerun()

st.session_state.etapas = st.data_editor(st.session_state.etapas, use_container_width=True, num_rows="dynamic")

# ==========================================
# 6. GERADOR MERMAID BLINDADO
# ==========================================
if len(st.session_state.etapas) > 0:
    st.divider()
    tipo_g = "graph LR" if orientacao == "Horizontal" else "graph TD"
    codigo = f"{tipo_g}\n"
    
    # Renderizar nós sanitizados
    for et in st.session_state.etapas:
        i = sanitize_mermaid_id(et['id'])
        t = sanitize_mermaid_text(et['texto'])
        cls = et.get('tipo', 'Processo')
        
        if cls == "Decisão": codigo += f'    {i}{{"{t}"}}\n'
        elif cls == "Início" or cls == "Fim": codigo += f'    {i}(["{t}"])\n'
        else: codigo += f'    {i}["{t}"]\n'
    
    # Renderizar conexões sanitizadas
    for et in st.session_state.etapas:
        if et.get('proxima'):
            for p in str(et['proxima']).split(","):
                p = p.strip()
                if not p: continue
                origem = sanitize_mermaid_id(et['id'])
                if "|" in p:
                    partes = p.split("|")
                    codigo += f"    {origem} -->|{partes[1]}| {sanitize_mermaid_id(partes[0])}\n"
                else:
                    codigo += f"    {origem} --> {sanitize_mermaid_id(p)}\n"

    renderizar_mermaid(codigo)
