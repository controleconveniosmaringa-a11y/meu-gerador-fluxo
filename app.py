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
# 2. MOTOR DE DESIGN (ESTÉTICA MIRO - GIGANTE)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=1200):
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
            /* Container configurado para permitir rolagem e não esmagar o gráfico */
            .mermaid {{ display: flex; justify-content: flex-start; overflow-x: auto; padding-bottom: 40px; }}
            .mermaid svg {{ min-width: 1500px !important; width: 100% !important; height: auto !important; }} 
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
                    fontFamily: 'Arial, sans-serif', 
                    fontSize: '20px', /* FONTE ENORME */
                    lineColor: '#94a3b8',
                    lineWidth: '3px', /* SETAS MAIS GROSSAS */
                    clusterBkg: 'transparent',
                    clusterBorder: '#cbd5e1'
                }},
                themeCSS: `
                    .node rect, .node circle, .node polygon, .node path {{ 
                        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
                    }}
                    .node label {{ padding: 16px !important; }} /* CAIXAS MUITO MAIORES */
                    .edgeLabel {{ background-color: #f4f5f9 !important; padding: 6px 12px !important; font-weight: bold; color: #475569; border: 1px solid #cbd5e1; border-radius: 6px; }}
                    .cluster rect {{ stroke-dasharray: 4; stroke-width: 2px; rx: 8px; ry: 8px; }}
                    .cluster text {{ font-weight: bold; fill: #64748b; font-size: 18px; padding: 15px; }}
                `,
                /* ESPAÇAMENTO GIGANTE ENTRE CAIXAS E SETAS */
                flowchart: {{ useMaxWidth: false, htmlLabels: true, curve: 'basis', nodeSpacing: 100, rankSpacing: 150 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (GABARITO BLINDADO ANTI-BLOCOS SOLTOS)
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Auditor Rigoroso de Processos BPMN. Sua missão é extrair um fluxo perfeito e SEM PONTAS SOLTAS.
    
    REGRAS ABSOLUTAS (SOB PENA DE FALHA GRAVE):
    1. INÍCIO E FIM OBRIGATÓRIOS: A primeira etapa TEM QUE SER do tipo "Início". A última etapa TEM QUE SER do tipo "Fim".
    2. PROIBIDO BLOCOS SOLTOS: Toda etapa (exceto o "Fim") DEVE ter o campo "proxima" preenchido com o ID da etapa seguinte. NUNCA deixe o campo "proxima" vazio. Se uma etapa encerra o processo, a "proxima" dela deve apontar para o ID da etapa de "Fim".
    3. CONDIÇÕES (SIM/NÃO): Se houver uma validação ou dúvida, crie uma "Decisão". O campo "proxima" DEVE ter as duas saídas: "ID_SIM|SIM, ID_NAO|NÃO".
    
    EXEMPLO GABARITO PERFEITO (Siga esta estrutura para não deixar blocos soltos):
    Texto: "Verifica se há saldo. Se SIM, paga. Se NÃO, cancela."
    JSON Correto:
    {{
      "fluxo": [
        {{"id": "1", "texto": "Início da verificação", "tipo": "Início", "raia": "Geral", "proxima": "2"}},
        {{"id": "2", "texto": "Há saldo?", "tipo": "Decisão", "raia": "Geral", "proxima": "3|SIM, 4|NÃO"}},
        {{"id": "3", "texto": "Paga o pedido", "tipo": "Processo", "raia": "Geral", "proxima": "5"}},
        {{"id": "4", "texto": "Cancela pedido", "tipo": "Processo", "raia": "Geral", "proxima": "5"}},
        {{"id": "5", "texto": "Fim do processo", "tipo": "Fim", "raia": "Geral", "proxima": ""}}
      ]
    }}
    
    Texto do usuário para analisar: {texto}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, # Mantém a lógica fria e estável
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
st.title("🎨 Gerador de Fluxos (Clone do Miro)")

orientacao = st.radio(
    "Orientação do Gráfico:", 
    ["Horizontal (Esquerda p/ Direita)", "Vertical (Cima p/ Baixo)"],
    horizontal=True,
    index=0 
)

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Cole o texto do seu processo aqui:", height=100)
    
    if st.button("✨ Gerar Fluxograma Exato", type="primary"):
        if texto.strip() != "":
            with st.spinner("Compilando lógica sem pontas soltas..."):
                resultado = processar_ia(texto)
                if resultado is not None and len(resultado) > 0:
                    st.session_state.etapas = resultado
                    st.rerun()
                elif resultado is not None and len(resultado) == 0:
                    st.warning("A IA não conseguiu estruturar as etapas.")
        else:
            st.warning("Por favor, digite um texto.")

with aba2:
    st.info("💡 **Dica:** Para dividir caminhos manualmente, use `ID|SIM, ID|NÃO` na coluna Próxima.")
    st.session_state.etapas = st.data_editor(
        st.session_state.etapas, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={
            "tipo": st.column_config.SelectboxColumn(
                "Tipo",
                options=["Início", "Processo", "Decisão", "Documento", "Fim"],
                required=True
            ),
            "proxima": st.column_config.TextColumn("Próxima (Use | para seta)")
        }
    )

# ==========================================
# 5. GERADOR MERMAID (CORES DO MIRO)
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
    
    tipo_g = "graph LR" if "Horizontal" in orientacao else "graph TD"
    codigo = f"{tipo_g}\n"
    
    codigo += "classDef Início fill:#a7f3d0,stroke:#059669,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Processo fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#1e293b,rx:8px,ry:8px;\n"
    codigo += "classDef Decisão fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Documento fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Fim fill:#a7f3d0,stroke:#059669,stroke-width:2px,color:#1e293b;\n\n"
    
    for nome_raia, nodes in raias.items():
        if nome_raia != 'Geral':
            nome_limpo = str(nome_raia).replace(" ", "_").replace("-", "_")
            codigo += f"subgraph {nome_limpo}[{nome_raia}]\n"
            
        for et in nodes:
            id_n = str(et['id']).replace(" ", "_")
            txt = str(et['texto']).replace('"', "'")
            cls = str(et.get('tipo', 'Processo'))
            
            if cls == "Decisão": 
                codigo += f'    {id_n}{{"{txt}"}}:::Decisão\n'
            elif cls == "Início":
                codigo += f'    {id_n}(["{txt}"]):::Início\n'
            elif cls == "Fim":
                codigo += f'    {id_n}(["{txt}"]):::Fim\n'
            elif cls == "Documento":
                codigo += f'    {id_n}[/"{txt}"/]:::Documento\n'
            else: 
                codigo += f'    {id_n}["{txt}"]:::Processo\n'
                
        if nome_raia != 'Geral':
            codigo += "end\n"
        
    for et in lista_de_etapas:
        if not et or "id" not in et: continue
        if et.get('proxima'):
            conexoes = str(et['proxima']).split(",") 
            for p in conexoes:
                p = p.strip()
                if p:
                    origem = str(et['id']).replace(' ', '_')
                    if "|" in p:
                        partes = p.split("|")
                        destino = partes[0].strip().replace(' ', '_')
                        rotulo = partes[1].strip()
                        codigo += f"    {origem} -->|{rotulo}| {destino}\n"
                    else:
                        destino = p.replace(' ', '_')
                        codigo += f"    {origem} --> {destino}\n"
    
    renderizar_mermaid(codigo)
