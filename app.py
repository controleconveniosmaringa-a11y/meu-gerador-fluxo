import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json

# ==========================================
# 1. CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Gerador de Fluxos de Processo", page_icon="📊", layout="wide")

if "etapas" not in st.session_state: 
    st.session_state.etapas = []

if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("⚠️ Configure sua GROQ_API_KEY no painel de Secrets do Streamlit.")
    st.stop()

# ==========================================
# 2. MOTOR DE DESIGN (GRANDE E CORPORATIVO)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=800):
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
            /* Permite rolagem em vez de esmagar o gráfico */
            .mermaid {{ display: flex; justify-content: flex-start; overflow-x: auto; padding-bottom: 20px; }}
            .mermaid svg {{ min-width: 1200px !important; height: auto !important; }} 
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
                    fontSize: '16px', /* Fonte maior e mais legível */
                    lineColor: '#64748b',
                    lineWidth: '3px', /* Setas mais encorpadas */
                    clusterBkg: '#ffffff',
                    clusterBorder: '#cbd5e1'
                }},
                themeCSS: `
                    /* Sombras e caixas mais espaçosas */
                    .node rect, .node circle, .node polygon, .node path {{ 
                        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
                    }}
                    .node label {{ padding: 10px !important; }}
                    /* Rótulos das setas (SIM/NÃO) maiores */
                    .edgeLabel {{ background-color: #ffffff !important; padding: 4px 10px !important; font-weight: bold; color: #1e293b; font-size: 14px; border-radius: 4px; border: 1px solid #e2e8f0; }}
                    .cluster rect {{ stroke-dasharray: 0; stroke-width: 2px; rx: 12px; ry: 12px; }}
                    .cluster text {{ font-weight: bold; fill: #475569; font-size: 16px; padding: 10px; }}
                `,
                /* Espaçamento extra entre as caixas para o gráfico não ficar amontoado */
                flowchart: {{ useMaxWidth: false, htmlLabels: true, curve: 'basis', nodeSpacing: 60, rankSpacing: 80 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (BLINDAGEM CONTRA O ERRO SIM/SEI)
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Arquiteto de Processos. Sua missão é estruturar o texto do usuário em um JSON perfeito.
    
    REGRAS DE OURO:
    1. LIGAÇÃO DO INÍCIO: Todo fluxo deve ter um nó do tipo "Início". O campo "proxima" deste nó DEVE OBRIGATORIAMENTE estar preenchido com o ID da etapa seguinte.
    2. CONDIÇÕES (DECISÃO): Se o texto indicar verificação ou cenário de "Se sim / Se não", você DEVE criar uma "Decisão".
       - No campo "proxima", mapeie as DUAS SAÍDAS usando ID|Texto.
       - EXTREMAMENTE IMPORTANTE: Use EXATAMENTE as palavras "SIM" e "NÃO" nas setas (Ex: "C|SIM, D|NÃO").
       - NUNCA confunda a palavra "SIM" com a palavra "SEI" (sistema).
    3. Documentos e sistemas (ex: SEI, Oxy) = usar tipo "Documento" apenas no campo "texto".
    
    Retorne um objeto JSON contendo APENAS a chave "fluxo".
    Estrutura exata do array: {{"id": "A", "texto": "Resumo", "tipo": "Processo", "raia": "Departamento", "proxima": "B"}}
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
st.title("📊 Gerador de Fluxos de Processo")

orientacao = st.radio(
    "Orientação do Gráfico:", 
    ["Horizontal (Esquerda p/ Direita)", "Vertical (Cima p/ Baixo)"],
    horizontal=True
)

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto_exemplo = "Ex: O setor de Compras inicia a solicitação. Verifica se há saldo? Se SIM, envia para a Tesouraria. Se NÃO, encerra o processo."
    texto = st.text_area("Descreva o processo de forma clara:", placeholder=texto_exemplo, height=100)
    
    if st.button("✨ Gerar Fluxograma", type="primary"):
        if texto.strip() != "":
            with st.spinner("Analisando as regras de negócio..."):
                resultado = processar_ia(texto)
                if resultado is not None and len(resultado) > 0:
                    st.session_state.etapas = resultado
                    st.rerun()
                elif resultado is not None and len(resultado) == 0:
                    st.warning("A IA não conseguiu estruturar as etapas. Tente detalhar o início e o fim.")
        else:
            st.warning("Por favor, digite um texto.")

with aba2:
    st.info("💡 **Dica:** Para dividir um caminho manualmente, escreva na coluna 'Próxima': `ID|SIM, ID|NÃO`")
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
            "proxima": st.column_config.TextColumn("Próxima (Use a barra reta | para texto na seta)")
        }
    )

# ==========================================
# 5. CONSTRUTOR MERMAID (RENDERIZAÇÃO)
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
    codigo += "classDef Fim fill:#fca5a5,stroke:#b91c1c,stroke-width:2px,color:#1e293b;\n\n"
    
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
                codigo += f'    {id_n}[/"{txt}"/]:::{cls}\n'
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
