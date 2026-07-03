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
# 2. MOTOR DE RENDERIZAÇÃO
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=900):
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
            .mermaid {{ display: flex; justify-content: center; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="mermaid">{codigo_mermaid}</div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true, theme: 'base',
                themeVariables: {{ fontFamily: 'Arial', fontSize: '18px', lineColor: '#94a3b8', lineWidth: '3px' }},
                flowchart: {{ useMaxWidth: false, curve: 'basis', nodeSpacing: 100, rankSpacing: 150 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. LÓGICA DA IA
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Arquiteto de Processos. Extraia o fluxo para JSON.
    Regras:
    1. Início e Fim são obrigatórios.
    2. Decisões têm as chaves "proxima_sim" e "proxima_nao" com IDs.
    3. Sistemas (SEI/Oxy) = Documento.
    4. Se o texto pedir para "acompanhar/verificar", crie um loop voltando para a etapa anterior no NÃO.
    
    Retorne JSON com chave "fluxo":
    {{"fluxo": [{{"id": "1", "texto": "Início", "tipo": "Início", "raia": "Geral", "proxima": "2"}}, ...]}}
    
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
        
        # Formata o SIM/NÃO para o gráfico
        for etapa in fluxo:
            if etapa.get("tipo") == "Decisão":
                sim = etapa.pop("proxima_sim", None)
                nao = etapa.pop("proxima_nao", None)
                if sim and nao: etapa["proxima"] = f"{sim}|SIM, {nao}|NÃO"
                elif sim: etapa["proxima"] = f"{sim}|SIM"
                elif nao: etapa["proxima"] = f"{nao}|NÃO"
        return fluxo
    except: return []

# ==========================================
# 4. INTERFACE PRINCIPAL
# ==========================================
st.title("📊 Gerador de Fluxos de Processo")

tab1, tab2 = st.tabs(["🤖 Gerador de IA", "✏️ Tabela de Edição"])

with tab1:
    texto = st.text_area("Descreva o seu processo aqui:", height=200, placeholder="Ex: O setor de compras inicia...")
    if st.button("✨ Gerar Fluxograma"):
        with st.spinner("Processando..."):
            st.session_state.etapas = processar_ia(texto)
            st.rerun()

with tab2:
    st.session_state.etapas = st.data_editor(st.session_state.etapas, num_rows="dynamic", use_container_width=True)

# ==========================================
# 5. CONSTRUTOR DE CÓDIGO
# ==========================================
if len(st.session_state.etapas) > 0:
    st.divider()
    
    # Blindagem Anti-Blocos Soltos
    id_fim = next((str(e["id"]) for e in st.session_state.etapas if e["tipo"] == "Fim"), "999")
    for et in st.session_state.etapas:
        if et["tipo"] != "Fim" and not str(et.get("proxima", "")).strip():
            et["proxima"] = id_fim

    codigo = "graph TD\n"
    # Cores
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
                    
    renderizar_mermaid(codigo)
