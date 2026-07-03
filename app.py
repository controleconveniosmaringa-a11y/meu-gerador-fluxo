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
# 2. MOTOR DE DESIGN BPMN (ESTÉTICA PREMIUM)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=900):
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; }}
            .mermaid {{ display: flex; justify-content: center; }}
        </style>
    </head>
    <body>
        <div class="mermaid">{codigo_mermaid}</div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'base',
                themeVariables: {{ 
                    fontFamily: 'Inter, system-ui, sans-serif', 
                    fontSize: '14px',
                    lineColor: '#64748b',
                    lineWidth: '2px',
                    clusterBkg: '#f8fafc',       /* Fundo das Raias/Departamentos */
                    clusterBorder: '#cbd5e1'     /* Borda das Raias */
                }},
                themeCSS: `
                    /* Sombras e transições para deixar visual de app caro */
                    .node rect, .node circle, .node polygon {{ 
                        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.08));
                        transition: all 0.3s ease;
                    }}
                    .node:hover rect, .node:hover circle, .node:hover polygon {{
                        filter: drop-shadow(0 6px 12px rgba(0,0,0,0.15));
                    }}
                    /* Ajuste fino dos textos e rótulos das setas */
                    .edgeLabel {{ background-color: #ffffff !important; padding: 3px 8px !important; border-radius: 6px; font-weight: 600; color: #334155; border: 1px solid #e2e8f0; }}
                    .cluster rect {{ rx: 8px; ry: 8px; stroke-width: 2px; }}
                    .cluster text {{ font-weight: bold; fill: #475569; }}
                `,
                flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis' }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (O CÉREBRO FORÇADO A PENSAR EM CONDIÇÕES)
# ==========================================
def processar_ia(texto):
    # Prompt rigoroso: Força a IA a procurar "Se" e criar ramificações
    prompt = f"""
    Você é um Analista de Processos Sênior. Sua tarefa é mapear fluxos complexos e você ODEIA fluxos em linha reta.
    REGRAS DE INTELIGÊNCIA VITAIS:
    1. CONDIÇÕES OBRIGATÓRIAS: Analise o texto rigorosamente. Se houver qualquer verificação, análise, aprovação ou possibilidade de erro, VOCÊ DEVE criar um nó do tipo "Decisão".
    2. BIFURCAÇÃO: Nós do tipo "Decisão" DEVEM obrigatoriamente ligar a dois caminhos (ex: proxima: "B, C").
    
    Retorne um objeto JSON com a chave "fluxo".
    Estrutura exata: {{"id": "A", "texto": "Resumo", "tipo": "Processo", "raia": "Departamento", "proxima": "B"}}
    Tipos permitidos: "Início", "Processo", "Decisão", "Fim"
    
    Processo do usuário: {texto}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, # Subimos um pouquinho a temperatura para ele ter criatividade na lógica
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
st.title("🏢 Gerador de Fluxos BPM (Inteligente & Premium)")

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Descreva o processo (Obrigue a IA a pensar, cite aprovações e validações):", height=100)
    if st.button("✨ Gerar Fluxo Inteligente", type="primary"):
        if texto.strip() != "":
            with st.spinner("A IA está mapeando condições e aprovações..."):
                resultado = processar_ia(texto)
                
                if resultado is not None and len(resultado) > 0:
                    st.session_state.etapas = resultado
                    st.rerun()
                elif resultado is not None and len(resultado) == 0:
                    st.warning("A IA não conseguiu extrair etapas desse texto.")
        else:
            st.warning("Por favor, digite um texto antes de gerar.")

with aba2:
    st.session_state.etapas = st.data_editor(
        st.session_state.etapas, 
        use_container_width=True, 
        num_rows="dynamic"
    )

# ==========================================
# 5. CONSTRUTOR DE CÓDIGO (APLICADOR DE ESTÉTICA)
# ==========================================
if len(st.session_state.etapas) > 0:
    st.divider()
    
    raias = {}
    lista_de_etapas = st.session_state.etapas
    
    for et in lista_de_etapas:
        if not et or "id" not in et: continue
        r = et.get('raia', 'Geral')
        if not r: r = 'Geral'
        if r not in raias: raias[r] = []
        raias[r].append(et)
    
    # Orientação padrão
    codigo = "graph TD\n"
    
    # === AQUI ESTÁ A MÁGICA DA BELEZA ===
    codigo += "classDef Início fill:#1e3a8a,stroke:#1e40af,stroke-width:2px,color:#ffffff;\n"
    codigo += "classDef Processo fill:#f0fdf4,stroke:#15803d,stroke-width:2px,color:#064e3b;\n"
    codigo += "classDef Decisão fill:#fffbeb,stroke:#b45309,stroke-width:2px,color:#78350f;\n"
    codigo += "classDef Fim fill:#7f1d1d,stroke:#991b1b,stroke-width:2px,color:#ffffff;\n\n"
    
    # Constrói as Raias
    for nome_raia, nodes in raias.items():
        nome_limpo = str(nome_raia).replace(" ", "_").replace("-", "_")
        codigo += f"subgraph {nome_limpo}[{nome_raia}]\n"
        
        for et in nodes:
            id_n = str(et['id']).replace(" ", "_")
            txt = str(et['texto']).replace('"', "'")
            cls = str(et.get('tipo', 'Processo'))
            
            # Aplica o formato correto e a cor (classDef) ao mesmo tempo!
            if cls == "Decisão": 
                codigo += f'    {id_n}{{"{txt}"}}:::Decisão\n'
            elif cls == "Início":
                codigo += f'    {id_n}(["{txt}"]):::Início\n'
            elif cls == "Fim":
                codigo += f'    {id_n}(["{txt}"]):::Fim\n'
            else: 
                codigo += f'    {id_n}["{txt}"]:::Processo\n'
                
        codigo += "end\n"
        
    # Adiciona Conexões
    for et in lista_de_etapas:
        if not et or "id" not in et: continue
        if et.get('proxima'):
            conexoes = str(et['proxima']).split(",")
            for p in conexoes:
                if p.strip():
                    origem = str(et['id']).replace(' ', '_')
                    destino = p.strip().replace(' ', '_')
                    codigo += f"{origem} --> {destino}\n"
    
    renderizar_mermaid(codigo)
