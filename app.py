import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json
import re

# ==========================================
# 1. CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Fluxo BPM Pro", page_icon="🏢", layout="wide")

if "etapas" not in st.session_state: 
    st.session_state.etapas = []

# Configuração Groq (Segurança)
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("⚠️ Configure sua GROQ_API_KEY no painel de Secrets do Streamlit.")
    st.stop()

# ==========================================
# 2. MOTOR DE DESIGN BPMN (CSS + SUBGRAPHS)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=800):
    html = f"""
    <html><body><div class="mermaid">{codigo_mermaid}</div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ 
            startOnLoad: true, theme: 'base',
            themeVariables: {{ 
                fontFamily: 'Inter, sans-serif', 
                primaryColor: '#f1f5f9',
                secondaryColor: '#e2e8f0'
            }},
            flowchart: {{ useMaxWidth: true, htmlLabels: true }}
        }});
    </script></body></html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA COM DEBUG ATIVADO E NOVO MODELO
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Analise o processo e retorne APENAS um JSON array.
    Estrutura: {{"id": "A", "texto": "Curto", "tipo": "Processo", "raia": "Departamento", "proxima": "B"}}
    Tipos permitidos: "Início", "Processo", "Decisão", "Fim"
    Processo: {texto}
    """
    try:
        # Trocamos para o modelo padrão da Groq que funciona em todas as contas gratuitas
        completion = client.chat.completions.create(
            model="llama-3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        res = completion.choices[0].message.content
        match = re.search(r'\[.*\]', res, re.DOTALL)
        if match: 
            return json.loads(match.group(0))
        else: 
            return []
    except Exception as e:
        # Agora o erro real será exposto na interface do Streamlit
        st.error(f"DETALHE DO ERRO DA API GROQ: {str(e)}")
        return []

# ==========================================
# 4. INTERFACE
# ==========================================
st.title("🏢 Gerador de Fluxos BPM (Swimlanes)")

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Descreva o processo (quem faz o quê):", height=100)
    if st.button("Gerar Fluxo BPM", type="primary"):
        if texto.strip() != "":
            with st.spinner("Estruturando o processo..."):
                st.session_state.etapas = processar_ia(texto)
                st.rerun()
        else:
            st.warning("Por favor, digite um texto antes de gerar.")

with aba2:
    st.session_state.etapas = st.data_editor(
        st.session_state.etapas, 
        use_container_width=True, 
        num_rows="dynamic"
    )

# ==========================================
# 5. GERADOR DE CÓDIGO BPM (Swimlanes)
# ==========================================
if st.session_state.etapas:
    st.divider()
    st.write("#### 📋 O Seu Fluxograma")
    
    # 1. Agrupar por Raia
    raias = {}
    for et in st.session_state.etapas:
        if not et or "id" not in et:
            continue
        r = et.get('raia', 'Geral')
        if r not in raias: raias[r] = []
        raias[r].append(et)
    
    # 2. Montar código Mermaid com subgraphs (Raias)
    codigo = "graph TD\n"
    for nome_raia, nodes in raias.items():
        # Limpa espaços e formata o nome da raia para o Mermaid aceitar
        nome_limpo = str(nome_raia).replace(" ", "_").replace("-", "_")
        codigo += f"subgraph {nome_limpo}[{nome_raia}]\n"
        
        for et in nodes:
            id_n = str(et['id']).replace(" ", "_")
            txt = str(et['texto']).replace('"', "'")
            cls = str(et.get('tipo', 'Processo'))
            
            if cls == "Decisão": 
                codigo += f'    {id_n}{{"{txt}"}}\n'
            elif cls == "Início" or cls == "Fim":
                codigo += f'    {id_n}(["{txt}"])\n'
            else: 
                codigo += f'    {id_n}["{txt}"]\n'
        codigo += "end\n"
        
    # 3. Adicionar conexões entre as caixas
    for et in st.session_state.etapas:
        if not et or "id" not in et:
            continue
        if et.get('proxima'):
            for p in str(et['proxima']).split(","):
                if p.strip():
                    codigo += f"{str(et['id']).replace(' ', '_')} --> {p.strip().replace(' ', '_')}\n"
    
    # Chama o renderizador final
    renderizar_mermaid(codigo)
