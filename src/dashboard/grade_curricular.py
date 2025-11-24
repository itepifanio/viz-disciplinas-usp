"""
Página para selecionar disciplinas por categoria e calcular créditos.
Layout Moderno com Sidebar, Abas e Indicadores de Meta.
"""

import pandas as pd
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
from streamlit_agraph import agraph, Node, Edge, Config

# Imports para WordCloud
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
import textwrap 

# --- CONFIGURAÇÃO INICIAL ---
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    from utils.config.subjects import obrigatorias, creditos_necessarios, creditos_obrigatorios
except ImportError:
    obrigatorias = []
    creditos_necessarios = 24
    creditos_obrigatorios = 8

# --- CAMINHOS ---
DATA_PATH = Path('src/data/grade_horaria/dados_dashboard_completo.pickle')
GRAPH_PATH = Path('src/data/grade_horaria/grafo_docentes_enrichido.graphml')
GRAPH_DISC_PATH = Path('src/data/grade_horaria/grafo_disciplinas_enrichido.graphml')

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def get_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    try:
        return pd.read_pickle(DATA_PATH)
    except Exception:
        return pd.DataFrame()

@st.cache_resource
def get_full_graph() -> nx.Graph:
    if not GRAPH_PATH.exists(): return None
    try: return nx.read_graphml(GRAPH_PATH)
    except Exception: return None

@st.cache_resource
def get_disc_graph() -> nx.Graph:
    if not GRAPH_DISC_PATH.exists(): return None
    try: return nx.read_graphml(GRAPH_DISC_PATH)
    except Exception: return None

# --- HELPERS VISUAIS ---
def get_hex_color(index, alpha=1.0):
    try:
        idx = int(float(index))
    except (ValueError, TypeError):
        if isinstance(index, str): idx = hash(index)
        else: return "#CCCCCC"
    
    if idx < 0: return "#CCCCCC"
    cmap = plt.get_cmap('tab20') 
    rgba = cmap(idx % 20)
    if alpha < 1.0:
        rgba = (rgba[0] + (1 - alpha) * (1 - rgba[0]),
                rgba[1] + (1 - alpha) * (1 - rgba[1]),
                rgba[2] + (1 - alpha) * (1 - rgba[2]), 1.0)
    return mcolors.to_hex(rgba)

def gerar_wordcloud(texto, titulo, colormap='viridis'):
    stop_words = set(stopwords.words('portuguese'))
    stop_words.update(stopwords.words('english'))
    stop_words.update(["de", "da", "do", "para", "que", "em", "um", "uma", "os", "as", "com", "na", "no", "ao", "aos", "pelo", "pela", "ser", "são", "dos", "das", "disciplina", "estudo", "analise", "curso"])
    if not texto or len(texto) < 5: return None
    wc = WordCloud(width=400, height=300, background_color='white', stopwords=stop_words, colormap=colormap, max_words=80, min_font_size=10).generate(texto)
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(titulo, fontsize=10, color='#333333', pad=10)
    plt.tight_layout(pad=0)
    return fig

# --- RENDERIZAÇÃO DE GRAFOS ---
def renderizar_mapa_disciplinas_geral(df_referencia):
    G = get_disc_graph()
    if G is None:
        st.warning("Grafo não encontrado.")
        return

    mapa_nomes = df_referencia.drop_duplicates('codigo').set_index('codigo')['disciplina'].to_dict()
    pos = nx.spring_layout(G, seed=42, k=0.15, iterations=60)
    SCALE = 600
    ag_nodes, ag_edges = [], []

    for node_id in G.nodes():
        data = G.nodes[node_id]
        is_selected = node_id in st.session_state.selecionadas
        comm_id = data.get('comunidade', data.get('modularity_class', -1))
        
        if is_selected:
            color, size, b_width, f_size = get_hex_color(comm_id, 1.0), 35, 3, 16
            font_color = "black"
        else:
            color, size, b_width, f_size = get_hex_color(comm_id, 0.4), 15, 1, 10
            font_color = "#AAAAAA"

        x_pos, y_pos = pos[node_id][0] * SCALE, pos[node_id][1] * SCALE
        nome_real = mapa_nomes.get(node_id, node_id)

        ag_nodes.append(Node(
            id=node_id, label=node_id, size=size, shape="dot", color=color,
            x=x_pos, y=y_pos, fixed=True, borderWidth=b_width, borderColor="#333333" if is_selected else "#DDDDDD",
            font={'color': font_color, 'size': f_size, 'face': 'arial'},
            title=f"{node_id}: {nome_real}"
        ))

    for u, v in G.edges():
        ag_edges.append(Edge(source=u, target=v, color="#E0E0E0", width=0.8))

    config = Config(width="100%", height=550, directed=False, physics=False, 
                   interaction={"dragNodes": False, "hover": True, "zoomView": True}, 
                   nodeHighlightBehavior=True, highlightColor="#F7CA18")
    
    selected = agraph(nodes=ag_nodes, edges=ag_edges, config=config)
    if selected:
        if selected in st.session_state.selecionadas: st.session_state.selecionadas.remove(selected)
        else: st.session_state.selecionadas.add(selected)
        st.rerun()

def renderizar_grafo_interativo(df_referencia):
    sel = list(st.session_state.selecionadas)
    if not sel:
        st.info("Selecione disciplinas para ver a rede.")
        return
    
    G_full = get_full_graph()
    if not G_full: return
    
    mapa_nomes = df_referencia.drop_duplicates('codigo').set_index('codigo')['disciplina'].to_dict()
    nos_exibir, docentes_viz = set(sel), set()
    cods_validos = [c for c in sel if c in G_full.nodes]

    for c in cods_validos:
        viz = list(G_full.neighbors(c))
        docentes_viz.update(viz)
        nos_exibir.update(viz)

    G_sub = G_full.subgraph(nos_exibir)
    try: pos = nx.shell_layout(G_sub, nlist=[list(docentes_viz), cods_validos])
    except: pos = nx.circular_layout(G_sub)
    
    SCALE = 300
    ag_nodes, ag_edges = [], []

    for n in G_sub.nodes():
        x, y = pos[n][0] * SCALE, pos[n][1] * SCALE
        if n in cods_validos:
            comm = G_sub.nodes[n].get('comunidade', -1)
            color = get_hex_color(comm)
            is_mand = str(G_sub.nodes[n].get('is_mandatory', 'False')).lower() == 'true'
            lbl = "\n".join(textwrap.wrap(mapa_nomes.get(n, n), width=20))
            ag_nodes.append(Node(id=n, label=lbl, size=40, shape="dot", color=color, x=x, y=y, fixed=True,
                               borderWidth=4 if is_mand else 2, borderColor="black" if is_mand else color,
                               font={'color': "black", 'size': 16, 'face': 'arial', 'background': 'white'}))
        else:
            ag_nodes.append(Node(id=n, label=n, size=20, shape="diamond", color="#34495e", x=x, y=y, fixed=True,
                               font={'color': "#555555", 'size': 14}))

    for u, v in G_sub.edges():
        ag_edges.append(Edge(source=u, target=v, color="#BDC3C7", width=2.0))

    config = Config(width="100%", height=600, directed=False, physics=False, interaction={"dragNodes": True, "hover": True, "zoomView": True})
    return agraph(nodes=ag_nodes, edges=ag_edges, config=config)

# --- LÓGICA DE CALLBACK ---
def atualizar_selecao(df_atual):
    if "editor_disciplinas" not in st.session_state: return
    edicoes = st.session_state["editor_disciplinas"]
    for idx, changes in edicoes.get('edited_rows', {}).items():
        if 'Selecionar' in changes:
            cod = df_atual.iloc[idx]['codigo']
            if changes['Selecionar']: st.session_state.selecionadas.add(cod)
            else: st.session_state.selecionadas.discard(cod)

# --- PÁGINA PRINCIPAL ---
st.set_page_config(layout="wide", page_title="Planejador Acadêmico")

if 'selecionadas' not in st.session_state: st.session_state.selecionadas = set()

df = get_data()

# --- SIDEBAR: FILTROS ---
with st.sidebar:
    st.header("🎛️ Filtros")
    st.info("Use os filtros para encontrar disciplinas na lista.")
    
    mapa_filtro = {'Comissão': 'commissao', 'Programa': 'nome_programa', 'Área de Concentração': 'area_concentracao'}
    tipo_filtro = st.selectbox("Filtrar por:", ['Selecione', 'Comissão', 'Programa', 'Área de Concentração'])
    
    item_selecionado = None
    if tipo_filtro != 'Selecione':
        col_df = mapa_filtro[tipo_filtro]
        opts = sorted(df[col_df].dropna().unique())
        item_selecionado = st.selectbox(f"Escolha {tipo_filtro}:", ['Selecione'] + opts)

    st.divider()
    st.markdown("### Ações")
    if st.button("🗑️ Limpar Seleção", use_container_width=True, type="primary"):
        st.session_state.selecionadas.clear()
        st.rerun()

# --- HEADER & KPIs (O "Placar") ---
st.title("🎓 Planejador Acadêmico")

# Dados dos KPIs
df_sel = df[df['codigo'].isin(st.session_state.selecionadas)]
soma_total = df_sel['n_creditos'].sum()
soma_obrig = df_sel[df_sel['codigo'].isin(obrigatorias)]['n_creditos'].sum()

# Lógica de Meta Atingida
meta_total_ok = soma_total >= creditos_necessarios
meta_obrig_ok = soma_obrig >= creditos_obrigatorios

cor_total = "normal" if not meta_total_ok else "off" # Trick do delta color
cor_obrig = "normal" if not meta_obrig_ok else "off"

symbol_total = "✅" if meta_total_ok else ""
symbol_obrig = "✅" if meta_obrig_ok else ""

# KPI Container
kpi_container = st.container()
with kpi_container:
    c1, c2, c3 = st.columns([1.5, 1.5, 1])
    
    with c1:
        st.metric(
            label=f"Créditos Totais {symbol_total}",
            value=f"{soma_total} / {creditos_necessarios}",
            delta="Meta Atingida!" if meta_total_ok else f"Faltam {max(0, creditos_necessarios - soma_total)}",
            delta_color="normal" if meta_total_ok else "off" # Verde se normal (que é positivo no streamlit)
        )
        st.progress(min(soma_total/creditos_necessarios, 1.0) if creditos_necessarios else 0)

    with c2:
        st.metric(
            label=f"Créditos Obrigatórios {symbol_obrig}",
            value=f"{soma_obrig} / {creditos_obrigatorios}",
            delta="Meta Atingida!" if meta_obrig_ok else f"Faltam {max(0, creditos_obrigatorios - soma_obrig)}",
            delta_color="normal" if meta_obrig_ok else "off"
        )
        st.progress(min(soma_obrig/creditos_obrigatorios, 1.0) if creditos_obrigatorios else 0)

    with c3:
        # Mini Pie Chart de Carga - Lógica ORIGINAL restaurada
        if not df_sel.empty:
            c_teorica = df_sel['carga_teorica'].sum() if 'carga_teorica' in df_sel.columns else 0
            c_pratica = df_sel['carga_pratica'].sum() if 'carga_pratica' in df_sel.columns else 0
            c_estudo = df_sel['carga_estudo'].sum() if 'carga_estudo' in df_sel.columns else 0
            
            if 'carga_total' in df_sel.columns:
                total_duracao = df_sel['carga_total'].sum()
            else:
                total_duracao = c_teorica + c_pratica + c_estudo
            
            if total_duracao > 0:
                valores = [c_teorica, c_pratica, c_estudo]
                colors = ['#3366CC', '#DC3912', '#109618']
                
                # Figura um pouco menor para caber no header, mas código igual
                fig, ax = plt.subplots(figsize=(3, 3)) 
                
                ax.pie(valores, autopct='%1.0f%%', startangle=90, colors=colors, 
                       wedgeprops=dict(width=0.35, edgecolor='w'), pctdistance=0.85)
                
                # Texto no centro
                ax.text(0, 0, f"{int(total_duracao)}h", ha='center', va='center', 
                        fontsize=14, fontweight='bold', color='#2c3e50')
                
                st.pyplot(fig, use_container_width=False)
                
                # Legenda original com 3 colunas e HTML spans
                sc1, sc2, sc3 = st.columns(3)
                sc1.caption(f"<span style='color:#3366CC'>⬤</span> Teórica: {int(c_teorica)}", unsafe_allow_html=True)
                sc2.caption(f"<span style='color:#DC3912'>⬤</span> Prática: {int(c_pratica)}", unsafe_allow_html=True)
                sc3.caption(f"<span style='color:#109618'>⬤</span> Estudo: {int(c_estudo)}", unsafe_allow_html=True)
            else:
                st.caption("Sem carga horária")
        else:
            st.caption("Sem disciplinas selecionadas")


st.divider()

# --- ABAS DE CONTEÚDO PRINCIPAL ---
tab_mapa, tab_tabela, tab_rede, tab_texto = st.tabs(["🗺️ Mapa Visual", "📋 Seleção por Lista", "🕸️ Rede de Docentes", "☁️ Análise Textual"])

with tab_mapa:
    st.markdown("#### Navegação Visual")
    st.caption("Clique nos nós para adicionar/remover da sua grade.")
    renderizar_mapa_disciplinas_geral(df)

with tab_tabela:
    st.markdown("#### Seleção via Tabela Filtrada")
    if item_selecionado and item_selecionado != 'Selecione':
        col_df = mapa_filtro[tipo_filtro]
        df_res = df[df[col_df] == item_selecionado].copy()
        if not df_res.empty:
            cols = ['codigo', 'disciplina', 'n_creditos']
            df_show = df_res[cols].copy()
            df_show['Selecionar'] = df_show['codigo'].isin(st.session_state.selecionadas)
            df_show = df_show[['Selecionar'] + cols]
            
            st.data_editor(
                df_show,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Selecionar": st.column_config.CheckboxColumn("Add", width="small"),
                    "codigo": st.column_config.TextColumn("Cód.", width="small"),
                    "disciplina": st.column_config.TextColumn("Nome", width="large"),
                    "n_creditos": st.column_config.NumberColumn("Cr", width="small")
                },
                key="editor_disciplinas",
                on_change=atualizar_selecao,
                args=(df_show,)
            )
        else:
            st.warning("Sem dados para este filtro.")
    else:
        st.info("👈 Selecione um filtro na barra lateral para ver a lista de disciplinas.")

with tab_rede:
    st.markdown("#### Quem ministra suas aulas?")
    renderizar_grafo_interativo(df)

with tab_texto:
    st.markdown("#### O que você vai estudar?")
    df_txt = df[df['codigo'].isin(st.session_state.selecionadas)]
    if not df_txt.empty:
        c1, c2, c3 = st.columns(3)
        if 'objetivos' in df_txt.columns: 
            with c1: st.pyplot(gerar_wordcloud(" ".join(df_txt['objetivos'].dropna().astype(str)), "Objetivos"), use_container_width=True)
        if 'justificativa' in df_txt.columns: 
            with c2: st.pyplot(gerar_wordcloud(" ".join(df_txt['justificativa'].dropna().astype(str)), "Justificativa", "magma"), use_container_width=True)
        if 'conteudo' in df_txt.columns: 
            with c3: st.pyplot(gerar_wordcloud(" ".join(df_txt['conteudo'].dropna().astype(str)), "Conteúdo", "cividis"), use_container_width=True)
    else:
        st.info("Selecione disciplinas para gerar a análise.")

# --- RESUMO FINAL ---
st.divider()
st.subheader("📑 Resumo da Sua Grade")

if not st.session_state.selecionadas:
    st.caption("Sua grade está vazia.")
else:
    df_final = df[df['codigo'].isin(st.session_state.selecionadas)].copy()
    
    # Cálculos finais
    if 'carga_total' not in df_final.columns:
        cc = [c for c in ['carga_teorica', 'carga_pratica', 'carga_estudo'] if c in df_final.columns]
        df_final['carga_total'] = df_final[cc].sum(axis=1) if cc else 0
        
    df_final['eh_obrigatoria'] = df_final['codigo'].isin(obrigatorias)
    
    # Enriquecimento com Docentes
    G_full_ref = get_full_graph()
    mapa_docentes = {}
    if G_full_ref:
        for cod in df_final['codigo']:
            if cod in G_full_ref:
                viz = list(G_full_ref.neighbors(cod))
                docs = [v for v in viz if v not in df['codigo'].values] # Assume que se não é código de disciplina, é prof
                mapa_docentes[cod] = ", ".join(docs)
            else: mapa_docentes[cod] = ""
    df_final['docentes_responsaveis'] = df_final['codigo'].map(mapa_docentes)

    # Display
    cols_final = ['codigo', 'disciplina', 'n_creditos', 'carga_total', 'eh_obrigatoria', 'docentes_responsaveis']
    df_display = df_final[cols_final].sort_values('eh_obrigatoria', ascending=False)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "codigo": st.column_config.TextColumn("Código", width="small"),
            "disciplina": st.column_config.TextColumn("Disciplina"),
            "n_creditos": st.column_config.NumberColumn("Créditos"),
            "carga_total": st.column_config.NumberColumn("Horas", format="%d h"),
            "eh_obrigatoria": st.column_config.CheckboxColumn("Obrig?", default=False),
            "docentes_responsaveis": st.column_config.TextColumn("Docentes"),
        }
    )

    # Botão Download
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Planilha (.csv)", csv, "minha_grade.csv", "text/csv")