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
                    fontSize: '15px', 
                    lineColor: '#94a3b8',
                    lineWidth: '2px', 
                    clusterBkg: '#ffffff',
                    clusterBorder: '#cbd5e1'
                }},
                themeCSS: `
                    .node rect, .node circle, .node polygon, .node path {{ 
                        filter: drop-shadow(0 3px 6px rgba(0,0,0,0.08));
                    }}
                    .node label {{ padding: 12px !important; }} 
                    .edgeLabel {{ background-color: #f4f5f9 !important; padding: 4px 8px !important; font-weight: bold; color: #475569; border: 1px solid #cbd5e1; border-radius: 4px; }}
                    .cluster rect {{ stroke-dasharray: 4; stroke-width: 1px; rx: 8px; ry: 8px; }}
                    .cluster text {{ font-weight: bold; fill: #64748b; font-size: 14px; padding: 10px; }}
                `,
                flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis', nodeSpacing: 60, rankSpacing: 90 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (BLINDADA CONTRA BUGS E ERROS LÓGICOS)
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Arquiteto BPMN Rigoroso. Extraia o fluxo para JSON.
    
    REGRAS DE OURO DA INTELIGÊNCIA:
    1. A primeira etapa TEM QUE SER "Início". NENHUMA ETAPA PODE APONTAR PARA O INÍCIO.
    2. A última etapa TEM QUE SER "Fim". O campo "proxima" do Fim DEVE ser uma string vazia "". Nunca use null.
    3. O SEGREDO DO LOOP: Se o texto disser para "acompanhar" ou "verificar se", divida em duas etapas:
       - Um "Processo" (Ex: Acompanhar conta-corrente).
       - Uma "Decisão" (Ex: Recurso entrou?). Na "Decisão", o SIM avança. O NÃO volta para o ID do Processo de acompanhamento.
    4. Decisões usam: "proxima_sim" e "proxima_nao".
    5. Sistemas (Oxy, SEI) geram tipo "Documento".
    
    EXEMPLO GABARITO PERFEITO:
    {{
      "fluxo": [
        {{"id": "1", "texto": "Início do fluxo", "tipo": "Início", "raia": "Geral", "proxima": "2"}},
        {{"id": "2", "texto": "Acompanhar conta-corrente", "tipo": "Processo", "raia": "Geral", "proxima": "3"}},
        {{"id": "3", "texto": "Recurso entrou?", "tipo": "Decisão", "raia": "Geral", "proxima_sim": "4", "proxima_nao": "2"}},
        {{"id": "4", "texto": "Lançamento no Oxy", "tipo": "Documento", "raia": "Geral", "proxima": "5"}},
        {{"id": "5", "texto": "Fim do processo", "tipo": "Fim", "raia": "Geral", "proxima": ""}}
      ]
    }}
    
    Texto do usuário: {texto}
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
        
        if not isinstance(fluxo, list):
            return []

        # --- FILTRO DE SANIDADE PYTHON (CORRIGE AS BURRICES DA IA) ---
        for etapa in fluxo:
            # 1. Remove qualquer "None" ou "null" que quebra o sistema
            for chave, valor in etapa.items():
                if valor is None:
                    etapa[chave] = ""
            
            # 2. Transforma o proxima_sim e proxima_nao em setas rotuladas
            if etapa.get("tipo") == "Decisão":
                sim = etapa.pop("proxima_sim", "")
                nao = etapa.pop("proxima_nao", "")
                
                if sim and nao:
                    etapa["proxima"] = f"{sim}|SIM, {nao}|NÃO"
                elif sim:
                    etapa["proxima"] = f"{sim}|SIM"
                elif nao:
                    etapa["proxima"] = f"{nao}|NÃO"
                    
        return fluxo
        
    except Exception as e:
        # Se a IA falhar feio, o Python não deixa o site cair
        return []

# ==========================================
# 4. INTERFACE E APLICATIVO
# ==========================================
st.title("🎨 Gerador de Fluxos")

orientacao = st.radio(
    "Orientação do Gráfico:", 
    ["Horizontal (Esquerda p/ Direita)", "Vertical (Cima p/ Baixo)"],
    horizontal=True,
    index=1 # Vertical como padrão
)

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Cole o texto do seu processo aqui:", height=200)
    
    if st.button("✨ Gerar Fluxograma Exato", type="primary"):
        if texto.strip() != "":
            with st.spinner("Estruturando processo rigorosamente..."):
                resultado = processar_ia(texto)
                # Só atualiza a tabela se a IA devolver um resultado válido, evitando tela branca
                if resultado and len(resultado) > 0:
                    st.session_state.etapas = resultado
                    st.rerun()
                else:
                    st.error("A IA não conseguiu estruturar as etapas corretamente. Tente novamente.")
        else:
            st.warning("Por favor, digite um texto.")

with aba2:
    st.info("💡 **Tabela de Edição:** Agora o sistema limpa erros de `None` automaticamente.")
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
# 5. GERADOR MERMAID & DOWNLOAD
# ==========================================
if len(st.session_state.etapas) > 0:
    st.divider()
    
    lista_de_etapas = st.session_state.etapas
    
    # BLINDAGEM EXTRA: Força caixas vazias a irem para o "Fim"
    id_fim = next((str(e["id"]) for e in lista_de_etapas if e["tipo"] == "Fim"), "999")
    if id_fim == "999":
        lista_de_etapas.append({"id": "999", "texto": "Fim do Processo", "tipo": "Fim", "raia": "Geral", "proxima": ""})
        
    for et in lista_de_etapas:
        if et["tipo"] != "Fim" and not str(et.get("proxima", "")).strip():
            et["proxima"] = id_fim

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
            
            if cls == "Decisão": codigo += f'    {id_n}{{"{txt}"}}:::Decisão\n'
            elif cls == "Início": codigo += f'    {id_n}(["{txt}"]):::Início\n'
            elif cls == "Fim": codigo += f'    {id_n}(["{txt}"]):::Fim\n'
            elif cls == "Documento": codigo += f'    {id_n}[/"{txt}"/]:::Documento\n'
            else: codigo += f'    {id_n}["{txt}"]:::Processo\n'
                
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
    
    col1, col2 = st.columns([8, 2])
    with col1:
        st.write("### 📋 Seu Fluxograma")
    with col2:
        st.download_button(
            label="📥 Baixar .mmd (Miro/Draw.io)",
            data=codigo,
            file_name="fluxo_miro.mmd",
            mime="text/plain",
            use_container_width=True
        )

    renderizar_mermaid(codigo)
