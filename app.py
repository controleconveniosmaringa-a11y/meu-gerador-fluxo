Opa! Eu sei exatamente o que aconteceu aqui. 😄

Você acabou copiando o meu **texto de conversa** junto com o código e colou tudo no GitHub! Como o Python só entende linguagem de programação, quando ele tentou ler a minha frase *"Você tem toda a razão!"* logo na linha 1, ele entrou em pânico e devolveu esse `SyntaxError` (Erro de Sintaxe).

Para o seu aplicativo funcionar, o arquivo `app.py` precisa receber **exclusivamente** o código, sem nenhuma palavra minha antes ou depois.

### Como resolver de forma garantida:

1. Vá ao seu arquivo `app.py` no GitHub e **apague absolutamente tudo** o que está lá.
2. Não selecione o texto arrastando o rato/mouse. Clique diretamente no botão **"Copy code"** (Copiar código) que aparece no canto superior direito desta caixa preta de código abaixo.
3. Cole no GitHub, faça o *Commit* (salvar) e pronto!

Aqui está o código limpinho e pronto para copiar:

```python
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
# 2. MOTOR DE DESIGN (ESTÉTICA CORPORATIVA)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=700):
    html = f"""
    <html>
    <head>
        <style>
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
                    lineColor: '#94a3b8',
                    lineWidth: '2px',
                    clusterBkg: 'transparent',
                    clusterBorder: '#cbd5e1'
                }},
                themeCSS: `
                    .node rect, .node circle, .node polygon, .node path {{ 
                        filter: drop-shadow(0 2px 5px rgba(0,0,0,0.06));
                    }}
                    .edgeLabel {{ background-color: #f4f5f9 !important; padding: 2px 6px !important; font-weight: bold; color: #475569; }}
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
# 3. IA (LÓGICA CONDICIONAL E LIGAÇÃO FORÇADA)
# ==========================================
def processar_ia(texto):
    prompt = f"""
    Você é um Arquiteto de Processos. Sua missão é estruturar o texto do usuário em um JSON perfeito.
    
    REGRAS DE OURO:
    1. LIGAÇÃO DO INÍCIO: Todo fluxo deve ter um nó do tipo "Início". O campo "proxima" deste nó DEVE OBRIGATORIAMENTE estar preenchido com o ID da etapa seguinte. O fluxo NUNCA pode começar quebrado.
    2. CONDIÇÕES (DECISÃO): Se o texto indicar verificação, validação ou cenário de "Se sim / Se não", você DEVE:
       - Criar uma etapa do tipo "Decisão".
       - No campo "proxima", mapear as DUAS SAÍDAS usando ID|Texto (Exemplo: "C|SIM, D|NÃO").
    3. Documentos, sistemas ou relatórios (ex: SEI, Oxy) = usar tipo "Documento".
    
    Retorne um objeto JSON contendo APENAS a chave "fluxo".
    Estrutura exata do array: {{"id": "A", "texto": "Resumo", "tipo": "Processo", "raia": "Departamento", "proxima": "B"}}
    Tipos de nó permitidos: "Início", "Processo", "Decisão", "Documento", "Fim"
    
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
            "proxima": st.column_config.TextColumn("Próxima (Use a barra reta | para criar texto na seta)")
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
            elif cls == "Início" or cls == "Fim":
                codigo += f'    {id_n}(["{txt}"]):::{cls}\n'
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

```
