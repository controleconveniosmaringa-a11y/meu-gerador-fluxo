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
# 2. MOTOR DE DESIGN (ESTÉTICA MIRO)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=900):
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
            .mermaid {{ display: flex; justify-content: center; overflow-x: auto; padding-bottom: 20px; }}
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
                    fontSize: '14px', 
                    lineColor: '#94a3b8',
                    lineWidth: '2px', 
                    clusterBkg: 'transparent',
                    clusterBorder: '#cbd5e1'
                }},
                themeCSS: `
                    .node rect, .node circle, .node polygon, .node path {{ 
                        filter: drop-shadow(0 2px 5px rgba(0,0,0,0.06));
                    }}
                    .node label {{ padding: 10px !important; }} 
                    .edgeLabel {{ background-color: #f4f5f9 !important; padding: 2px 8px !important; font-weight: normal; color: #475569; }}
                    .cluster rect {{ stroke-dasharray: 4; stroke-width: 1px; rx: 8px; ry: 8px; }}
                    .cluster text {{ font-weight: bold; fill: #64748b; font-size: 14px; padding: 10px; }}
                `,
                flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis', nodeSpacing: 50, rankSpacing: 70 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (GABARITO DO LOOP)
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Arquiteto BPMN Rigoroso. Extraia o fluxo para JSON.
    
    REGRAS DE OURO DA INTELIGÊNCIA:
    1. INÍCIO E FIM: A primeira etapa TEM QUE SER "Início", a última TEM QUE SER "Fim".
    2. O SEGREDO DO LOOP (ACOMPANHAR/ESPERAR): Se o texto disser para "acompanhar" ou "verificar se", divida em duas etapas:
       - Uma etapa tipo "Processo" (Ex: Acompanhar conta-corrente).
       - Uma etapa tipo "Decisão" logo abaixo (Ex: Recurso entrou na conta?).
       - Na "Decisão", o SIM avança. O NÃO volta para o ID do Processo de acompanhamento.
    3. REGRAS DE JSON:
       - Decisões usam as chaves: "proxima_sim" e "proxima_nao".
       - Outros tipos usam apenas a chave: "proxima".
    4. SISTEMAS: Referências a sistemas (Oxy, SEI) geram tipo "Documento".
    
    EXEMPLO GABARITO:
    {{
      "fluxo": [
        {{"id": "1", "texto": "Início do fluxo", "tipo": "Início", "raia": "Geral", "proxima": "2"}},
        {{"id": "2", "texto": "Encaminhar para a tesouraria", "tipo": "Processo", "raia": "Geral", "proxima": "3"}},
        {{"id": "3", "texto": "Acompanhar conta-corrente do convênio", "tipo": "Processo", "raia": "Geral", "proxima": "4"}},
        {{"id": "4", "texto": "Recurso entrou na conta?", "tipo": "Decisão", "raia": "Geral", "proxima_sim": "5", "proxima_nao": "3"}},
        {{"id": "5", "texto": "Realizar lançamento de transferência bancária no sistema Oxy", "tipo": "Documento", "raia": "Geral", "proxima": "6"}},
        {{"id": "6", "texto": "Fim da execução", "tipo": "Fim", "raia": "Geral", "proxima": ""}}
      ]
    }}
    
    Texto do usuário para analisar: {texto}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, 
            response_format={"type": "json_object"} 
        )
        
        res_texto = completion.choices[0].message.content
        dados = json.loads(res_texto)
        fluxo = dados.get("fluxo", []) 
        
        for etapa in fluxo:
            if etapa.get("tipo") == "Decisão":
                sim = etapa.pop("proxima_sim", None)
                nao = etapa.pop("proxima_nao", None)
                
                if sim and nao:
                    etapa["proxima"] = f"{sim}|SIM, {nao}|NÃO"
                elif sim:
                    etapa["proxima"] = f"{sim}|SIM"
                elif nao:
                    etapa["proxima"] = f"{nao}|NÃO"
                    
        return fluxo
        
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
    index=1 
)

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Cole o texto do seu processo aqui:", height=200)
    
    if st.button("✨ Gerar Fluxograma Exato", type="primary"):
        if texto.strip() != "":
            with st.spinner("Estruturando processo (sem pontas soltas)..."):
                resultado = processar_ia(texto)
                if resultado is not None and len(resultado) > 0:
                    st.session_state.etapas = resultado
                    st.rerun()
                elif resultado is not None and len(resultado) == 0:
                    st.warning("A IA não conseguiu estruturar as etapas.")
        else:
            st.warning("Por favor, digite um texto.")

with aba2:
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
# 5. GERADOR MERMAID & BLINDAGEM PYTHON
# ==========================================
if len(st.session_state.etapas) > 0:
    st.divider()
    
    lista_de_etapas = st.session_state.etapas
    
    # --- BLINDAGEM ANTI-BLOCOS SOLTOS (100% PYTHON) ---
    # 1. Verifica se existe um nó de "Fim"
    id_fim = None
    for et in lista_de_etapas:
        if et and et.get("tipo") == "Fim":
            id_fim = str(et["id"])
            break
            
    # 2. Se a IA esqueceu de criar o Fim, o Python cria um!
    if not id_fim:
        id_fim = "999"
        lista_de_etapas.append({
            "id": id_fim, "texto": "Fim do Processo", 
            "tipo": "Fim", "raia": "Geral", "proxima": ""
        })
        
    # 3. Varre todas as etapas e amarra as que estão soltas ao Fim
    for et in lista_de_etapas:
        if et and et.get("tipo") != "Fim":
            prox = str(et.get("proxima", "")).strip()
            if not prox: 
                et["proxima"] = id_fim
    # ---------------------------------------------------

    raias = {}
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
    
    # 6. BOTÃO DE DOWNLOAD (NOVIDADE)
    col1, col2 = st.columns([8, 2])
    with col1:
        st.write("### 📋 Seu Fluxograma")
    with col2:
        st.download_button(
            label="📥 Baixar Arquivo",
            data=codigo,
            file_name="meu_fluxo.mmd",
            mime="text/plain",
            help="Arquivo original que pode ser aberto em qualquer editor corporativo, como o Draw.io ou Miro."
        )

    renderizar_mermaid(codigo)
