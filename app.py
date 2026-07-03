import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json

# ==========================================
# 1. CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Fluxo BPM Pro", page_icon="🏢", layout="wide")

if "etapas" not in st.session_state: 
    st.session_state.etapas = []

# Configuração Groq
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("⚠️ Configure sua GROQ_API_KEY no painel de Secrets do Streamlit.")
    st.stop()

# ==========================================
# 2. MOTOR DE DESIGN BPMN
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
# 3. IA COM MODELO CORRIGIDO (Llama 3.1)
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Analise o processo e retorne um objeto JSON.
    Obrigatório ter uma chave chamada "fluxo" contendo um array de etapas.
    Estrutura exata de cada etapa no array: {{"id": "A", "texto": "Resumo", "tipo": "Processo", "raia": "Departamento", "proxima": "B"}}
    Tipos de nó permitidos: "Início", "Processo", "Decisão", "Fim"
    Processo do usuário: {texto}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"} 
        )
        
        res_texto = completion.choices[0].message.content
        dados = json.loads(res_texto)
        return dados.get("fluxo", []) 
        
    except Exception as e:
        st.error(f"Erro ao conectar com a IA: {str(e)}")
        return None

# ==========================================
# 4. INTERFACE
# ==========================================
st.title("🏢 Gerador de Fluxos BPM (Swimlanes)")

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Descreva o processo (quem faz o quê):", height=100)
    if st.button("Gerar Fluxo BPM", type="primary"):
        if texto.strip() != "":
            with st.spinner("A IA está estruturando o processo..."):
                resultado = processar_ia(texto)
                
                if resultado is not None and len(resultado) > 0:
                    st.session_state.etapas = resultado
                    st.rerun()
                elif resultado is not None and len(resultado) == 0:
                    st.warning("A IA não conseguiu extrair etapas desse texto. Tente detalhar mais.")
        else:
            st.warning("Por favor, digite um texto antes de gerar.")

with aba2:
    st.session_state.etapas = st.data_editor(
        st.session_state.etapas, 
        use_container_width=True, 
        num_rows="dynamic"
    )

# ==========================================
# 5. GERADOR DE CÓDIGO BPM
# ==========================================
if len(st.session_state.etapas) > 0:
    st.divider()
    st.write("#### 📋 O Seu Fluxograma BPM")
    
    raias = {}
    lista_de_etapas = st.session_state.etapas
    
    for et in lista_de_etapas:
        if not et or "id" not in et:
            continue
        r = et.get('raia', 'Geral')
        if not r: 
            r = 'Geral'
        if r not in raias: 
            raias[r] = []
        raias[r].append(et)
    
    codigo = "graph TD\n"
    
    for nome_raia, nodes in raias.items():
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
        
    for et in lista_de_etapas:
        if not et or "id" not in et:
            continue
        if et.get('proxima'):
            conexoes = str(et['proxima']).split(",")
            for p in conexoes:
                if p.strip():
                    origem = str(et['id']).replace(' ', '_')
                    destino = p.strip().replace(' ', '_')
                    codigo += f"{origem} --> {destino}\n"
    
    renderizar_mermaid(
