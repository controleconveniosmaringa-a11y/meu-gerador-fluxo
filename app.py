Entendido, alto e claro. **Zero** alterações na inteligência, **zero** alterações na lógica. Mexi exclusivamente na "lente de aumento" do código.

Para deixar o fluxo gigante, eu fiz apenas estas três alterações de design no CSS:

1. **Largura forçada:** Aumentei o mínimo de `1000px` para `1800px`.
2. **Fontes:** Pulei a fonte de `15px` para `18px` e o espaçamento interno das caixas.
3. **Respiro (Espaçamento):** Aumentei a distância entre as etapas (`nodeSpacing` e `rankSpacing`) para o fluxo esticar mais na tela.

### O Código (Apenas Maior)

Apague o código antigo, use o botão **"Copy code"** aqui no canto e cole no seu arquivo:

```python
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
# 2. MOTOR DE DESIGN (ESTÉTICA MIRO - TAMANHO GIGANTE)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=1000):
    html = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; background-color: #f4f5f9; }}
            .mermaid {{ display: flex; justify-content: flex-start; overflow-x: auto; padding-bottom: 20px; }}
            /* AQUI ESTÁ O AUMENTO: Largura mínima forçada para 1800px para não esmagar o gráfico */
            .mermaid svg {{ min-width: 1800px !important; height: auto !important; }} 
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
                    fontSize: '18px', /* AQUI: Fonte aumentada */
                    lineColor: '#94a3b8',
                    lineWidth: '2px',
                    clusterBkg: 'transparent',
                    clusterBorder: '#cbd5e1'
                }},
                themeCSS: `
                    .node rect, .node circle, .node polygon, .node path {{ 
                        filter: drop-shadow(0 2px 5px rgba(0,0,0,0.08));
                    }}
                    .node label {{ padding: 12px !important; }} /* AQUI: Caixas mais "gordinhas" */
                    .edgeLabel {{ background-color: #f4f5f9 !important; padding: 4px 10px !important; font-weight: bold; color: #475569; border: 1px solid #cbd5e1; border-radius: 4px; }}
                    .cluster rect {{ stroke-dasharray: 4; stroke-width: 1px; rx: 8px; ry: 8px; }}
                    .cluster text {{ font-weight: bold; fill: #64748b; font-size: 16px; padding: 10px; }}
                `,
                /* AQUI: Mais espaço em branco entre as setas e as caixas */
                flowchart: {{ useMaxWidth: false, htmlLabels: true, curve: 'basis', nodeSpacing: 80, rankSpacing: 120 }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (GABARITO INJETADO + TEMP 0.0) - INTACTO
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Arquiteto de Processos especialista em BPMN. Extraia o fluxo do texto para um JSON.
    
    REGRA CRÍTICA PARA CONDIÇÕES (SIM/NÃO):
    Sempre que o texto apresentar uma validação, dúvida ou pergunta (Ex: "Recurso entrou na conta?"):
    1. Crie uma etapa com o tipo "Decisão".
    2. Conecte AS DUAS SAÍDAS no campo "proxima" usando o formato "ID_DO_SIM|SIM, ID_DO_NAO|NÃO".
    
    EXEMPLO OBRIGATÓRIO DE COMO VOCÊ DEVE RESPONDER (Copie esta estrutura):
    Texto: "Verifica se há saldo. Se SIM, paga. Se NÃO, cancela."
    JSON Correto:
    {{
      "fluxo": [
        {{"id": "A", "texto": "Verifica se há saldo", "tipo": "Decisão", "raia": "Geral", "proxima": "B|SIM, C|NÃO"}},
        {{"id": "B", "texto": "Paga", "tipo": "Processo", "raia": "Geral", "proxima": ""}},
        {{"id": "C", "texto": "Cancela", "tipo": "Processo", "raia": "Geral", "proxima": ""}}
      ]
    }}
    
    OUTRAS REGRAS:
    - Sistemas (SEI, Oxy, planilhas) = tipo "Documento".
    - Loops: Se a resposta NÃO disser para voltar a uma etapa anterior, coloque o ID da etapa antiga.
    
    Texto para analisar: {texto}
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
        return dados.get("fluxo", []) 
        
    except Exception as e:
        st.error(f"Erro ao conectar com a IA: {str(e)}")
        return None

# ==========================================
# 4. INTERFACE - INTACTO
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
            with st.spinner("Compilando lógica de ramificações (SIM/NÃO)..."):
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
# 5. GERADOR MERMAID (CORES DO MIRO) - INTACTO
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

```
