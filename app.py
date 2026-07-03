import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json

# ==========================================
# 1. CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Gerador de Fluxos (Estilo Miro)", page_icon="🎨", layout="wide")

if "etapas" not in st.session_state: 
    st.session_state.etapas = []

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("⚠️ Configure sua GROQ_API_KEY no painel de Secrets do Streamlit.")
    st.stop()

# ==========================================
# 2. MOTOR DE DESIGN (CLONE DO MIRO)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=900):
    html = f"""
    <html>
    <head>
        <style>
            /* Fundo suave idêntico ao canvas do Miro */
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
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
                    fontFamily: 'Arial, sans-serif', 
                    fontSize: '13px',
                    lineColor: '#94a3b8', /* Cinza das setas */
                    lineWidth: '2px',
                    clusterBkg: 'transparent',
                    clusterBorder: '#cbd5e1'
                }},
                themeCSS: `
                    /* Sombra idêntica aos cards do Miro */
                    .node rect, .node circle, .node polygon, .node path {{ 
                        filter: drop-shadow(0 2px 5px rgba(0,0,0,0.06));
                    }}
                    /* Textos flutuantes nas setas sem fundo branco forte */
                    .edgeLabel {{ background-color: #f4f5f9 !important; padding: 2px 6px !important; font-weight: normal; color: #475569; }}
                    /* Raias mais discretas para não atrapalhar o visual clean */
                    .cluster rect {{ stroke-dasharray: 4; stroke-width: 1px; }}
                    .cluster text {{ font-weight: bold; fill: #64748b; font-size: 14px; }}
                `,
                flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis' }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA ATUALIZADA (COM TEXTOS NAS SETAS E DOCUMENTOS)
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Analista mapeando fluxos de sistemas.
    REGRAS DE FORMATAÇÃO:
    1. Se houver geração, anexo ou leitura de arquivo (ex: processo SEI, relatórios, sistema Oxy), use o tipo "Documento".
    2. Se houver verificações, use "Decisão".
    3. Para escrever nas setas (como "SIM" ou "NÃO"), coloque um pipe `|` e o texto na chave proxima. Exemplo: "B|SIM, C|NÃO".
    
    Retorne um objeto JSON com a chave "fluxo".
    Estrutura: {{"id": "A", "texto": "Resumo", "tipo": "Processo", "raia": "", "proxima": "B|Verificar"}}
    Tipos permitidos: "Início", "Processo", "Decisão", "Documento", "Fim"
    
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
st.title("🎨 Gerador de Fluxos (Visual Miro)")

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Descreva o processo (Opcional: cite onde devem ter anexos ou sistemas):", height=100)
    if st.button("✨ Gerar Fluxo Estilo Miro", type="primary"):
        if texto.strip() != "":
            with st.spinner("Desenhando o canvas..."):
                resultado = processar_ia(texto)
                if resultado is not None and len(resultado) > 0:
                    st.session_state.etapas = resultado
                    st.rerun()
                elif resultado is not None and len(resultado) == 0:
                    st.warning("A IA não conseguiu extrair etapas.")
        else:
            st.warning("Por favor, digite um texto.")

with aba2:
    st.info("💡 **Dica:** Para colocar texto numa seta, escreva na coluna 'Próxima' assim: `ID|Texto` (Ex: `C|SIM`)")
    st.session_state.etapas = st.data_editor(
        st.session_state.etapas, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={
            "tipo": st.column_config.SelectboxColumn(
                "Tipo de Nó",
                options=["Início", "Processo", "Decisão", "Documento", "Fim"],
                required=True
            ),
            "proxima": st.column_config.TextColumn("Próxima (Use ID|Texto para setas)")
        }
    )

# ==========================================
# 5. GERADOR DE CÓDIGO (APLICADOR DE ESTÉTICA MIRO)
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
    
    codigo = "graph TD\n"
    
    # === AQUI ESTÃO AS CORES EXATAS DA SUA IMAGEM ===
    codigo += "classDef Início fill:#a7f3d0,stroke:#059669,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Processo fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#1e293b,rx:8px,ry:8px;\n"
    codigo += "classDef Decisão fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Documento fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#1e293b;\n"
    codigo += "classDef Fim fill:#a7f3d0,stroke:#059669,stroke-width:2px,color:#1e293b;\n\n"
    
    # Montagem dos nós
    for nome_raia, nodes in raias.items():
        if nome_raia != 'Geral':
            nome_limpo = str(nome_raia).replace(" ", "_").replace("-", "_")
            codigo += f"subgraph {nome_limpo}[{nome_raia}]\n"
            
        for et in nodes:
            id_n = str(et['id']).replace(" ", "_")
            txt = str(et['texto']).replace('"', "'")
            cls = str(et.get('tipo', 'Processo'))
            
            # Formatos visuais (Pílula, Retângulo Arredondado, Losango, Paralelogramo)
            if cls == "Decisão": 
                codigo += f'    {id_n}{{"{txt}"}}:::Decisão\n'
            elif cls == "Início" or cls == "Fim":
                codigo += f'    {id_n}(["{txt}"]):::{cls}\n'
            elif cls == "Documento":
                codigo += f'    {id_n}[/"{txt}"/]:::{cls}\n' # Paralelogramo para sistemas/anexos
            else: 
                codigo += f'    {id_n}["{txt}"]:::Processo\n'
                
        if nome_raia != 'Geral':
            codigo += "end\n"
        
    # Montagem das Setas com suporte a textos (SIM, NÃO, etc)
    for et in lista_de_etapas:
        if not et or "id" not in et: continue
        if et.get('proxima'):
            conexoes = str(et['proxima']).split(",")
            for p in conexoes:
                p = p.strip()
                if p:
                    origem = str(et['id']).replace(' ', '_')
                    # Verifica se o usuário ou a IA colocou o Pipe (|) para texto na seta
                    if "|" in p:
                        partes = p.split("|")
                        destino = partes[0].strip().replace(' ', '_')
                        rotulo = partes[1].strip()
                        codigo += f"    {origem} -->|{rotulo}| {destino}\n"
                    else:
                        destino = p.replace(' ', '_')
                        codigo += f"    {origem} --> {destino}\n"
    
    renderizar_mermaid(codigo)
