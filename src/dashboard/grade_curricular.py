"""
Página para selecionar disciplinas por categoria e calcular créditos.
Inclui visualização de rede Docentes x Disciplinas corrigida.
"""

import pandas as pd
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
from streamlit_agraph import agraph, Node, Edge, Config

# Import de configs do projeto
from utils.config.subjects import obrigatorias, creditos_necessarios, creditos_obrigatorios

# --- CAMINHOS DOS ARQUIVOS ---
DATA_PATH = Path('src/data/grade_horaria/dados_dashboard_completo.pickle')
GRAPH_PATH = Path('src/data/grade_horaria/grafo_docentes_enrichido.graphml')

# --- FUNÇÕES DE CARREGAMENTO (CACHE) ---

@st.cache_data
def get_data() -> pd.DataFrame:
    """Carrega os dados da tabela."""
    if not DATA_PATH.exists():
        st.error(f"Arquivo de dados não encontrado em: {DATA_PATH}")
        return pd.DataFrame(columns=['commissao', 'nome_programa', 'area_concentracao', 'codigo', 'disciplina', 'n_creditos'])
    try:
        return pd.read_pickle(DATA_PATH)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_resource
def get_full_graph() -> nx.Graph:
    """Carrega o grafo completo do disco."""
    if not GRAPH_PATH.exists():
        return None
    try:
        return nx.read_graphml(GRAPH_PATH)
    except Exception:
        return None

# --- FUNÇÕES AUXILIARES DO GRAFO ---

def get_hex_color(index):
    """Gera cor consistente baseada no ID da comunidade."""
    try:
        idx = int(index)
    except:
        return "#CCCCCC"
    
    if idx < 0: return "#CCCCCC"
    
    # Paleta 'tab20' tem 20 cores distintas. Cicla se passar de 20.
    cmap = plt.get_cmap('tab20') 
    return mcolors.to_hex(cmap(idx % 20))

def renderizar_grafo_interativo(df_filtrado):
    """
    Desenha o grafo filtrado estritamente pelas disciplinas visíveis.
    """
    G_full = get_full_graph()
    
    if G_full is None:
        st.warning("Arquivo de grafo (.graphml) não encontrado. Rode o pipeline.")
        return

    # 1. Lista exata de códigos que estão na tabela filtrada
    codigos_no_filtro = set(df_filtrado['codigo'].astype(str).str.strip())
    
    if not codigos_no_filtro:
        st.info("Nenhuma disciplina no filtro atual.")
        return

    ag_nodes = []
    ag_edges = []
    
    # Conjuntos para evitar duplicatas na visualização
    added_nodes = set()
    added_edges = set()

    # 2. Construção do Subgrafo
    # Iteramos APENAS sobre os códigos do filtro para garantir que o grafo obedeça a tabela
    for codigo in codigos_no_filtro:
        if codigo not in G_full.nodes:
            continue # Pula se por algum motivo o nó não estiver no grafo

        # --- Adiciona o Nó da Disciplina ---
        if codigo not in added_nodes:
            data = G_full.nodes[codigo]
            
            # Recupera metadados
            comm_id = int(data.get('community', -1))
            color = get_hex_color(comm_id)
            
            # Check de Obrigatória (trata string 'True'/'False' ou bool)
            is_mandatory = data.get('is_mandatory', False)
            if isinstance(is_mandatory, str):
                is_mandatory = is_mandatory.lower() == 'true'
            
            label_disc = data.get('label', codigo)

            ag_nodes.append(Node(
                id=codigo,
                label=codigo, # Mostra o código no nó
                size=35 if is_mandatory else 20,
                shape="dot",
                color=color,
                borderWidth=3 if is_mandatory else 1,
                borderColor="#000000" if is_mandatory else color,
                title=f"Disciplina: {label_disc}\nComunidade: {comm_id}\nObrigatória: {is_mandatory}" # Tooltip
            ))
            added_nodes.add(codigo)

        # --- Adiciona os Docentes Conectados ---
        # Pega vizinhos (no grafo bipartido, vizinhos de disciplina são sempre docentes)
        for docente_id in G_full.neighbors(codigo):
            
            # Adiciona nó do Docente (se ainda não foi adicionado)
            if docente_id not in added_nodes:
                ag_nodes.append(Node(
                    id=docente_id,
                    label=docente_id,
                    size=15,
                    shape="diamond",
                    color="#444444", # Cinza escuro
                    title=f"Docente: {docente_id}"
                ))
                added_nodes.add(docente_id)
            
            # Adiciona Aresta
            edge_key = tuple(sorted((codigo, docente_id)))
            if edge_key not in added_edges:
                ag_edges.append(Edge(
                    source=codigo, 
                    target=docente_id, 
                    color="#EEEEEE"
                ))
                added_edges.add(edge_key)

    # 3. Validação de Tamanho
    if len(ag_nodes) > 200:
        st.warning(f"⚠️ O grafo possui {len(ag_nodes)} nós. Pode ficar lento. Refine o filtro (ex: filtre por Área de Concentração).")

    # 4. Configuração Visual
    config = Config(
        width="100%",
        height=600,
        directed=False,
        physics=True,
        hierarchy=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        physicsOptions={
            "barnesHut": {
                "gravitationalConstant": -2000,
                "centralGravity": 0.3,
                "springLength": 95
            },
            "minVelocity": 0.75
        }
    )

    return agraph(nodes=ag_nodes, edges=ag_edges, config=config)


# --- INTERFACE PRINCIPAL ---

def setup_new_filters(df):
    st.subheader("1. Filtros de Busca")
    col1, col2 = st.columns(2)

    mapa_filtro = {
        'Comissão': 'commissao',
        'Programa': 'nome_programa',
        'Área de Concentração': 'area_concentracao'
    }

    with col1:
        tipo_filtro = st.selectbox(
            "Filtrar por:",
            options=['Selecione um tipo', 'Comissão', 'Programa', 'Área de Concentração']
        )
    
    item_selecionado = None
    with col2:
        if tipo_filtro == 'Selecione um tipo':
            st.selectbox("Selecione o item:", options=['--'], disabled=True)
        else:
            coluna_df = mapa_filtro[tipo_filtro]
            if coluna_df in df.columns:
                opcoes = sorted(df[coluna_df].dropna().unique())
                item_selecionado = st.selectbox(f"Selecione o {tipo_filtro}:", options=['Selecione'] + opcoes)
            else:
                st.warning(f"Coluna {coluna_df} não encontrada.")
            
    return tipo_filtro, item_selecionado

# --- CONFIGURAÇÃO DA PÁGINA ---

st.set_page_config(layout="wide", page_title="Planejador de Disciplinas")

if 'selecionadas' not in st.session_state:
    st.session_state.selecionadas = set()

st.title("Planejador de Disciplinas & Visualização de Rede")

df = get_data()

if df.empty:
    st.error("Não foi possível carregar os dados.")
else:
    # --- CALLBACK ---
    def atualizar_selecao(df_tabela_atual):
        if "editor_disciplinas" not in st.session_state: return
        edicoes = st.session_state["editor_disciplinas"]
        for index_editado, edicao in edicoes.get('edited_rows', {}).items():
            if 'Selecionar' in edicao:
                try:
                    codigo = df_tabela_atual.iloc[index_editado]['codigo']
                    if edicao['Selecionar']: st.session_state.selecionadas.add(codigo)
                    else: st.session_state.selecionadas.discard(codigo)
                except IndexError: continue

    # --- ÁREA DE FILTROS E TABELA ---
    tipo_filtro, item_selecionado = setup_new_filters(df)
    
    df_resultado = pd.DataFrame() # Inicializa vazio

    if item_selecionado and item_selecionado != 'Selecione':
        coluna_df = {
            'Comissão': 'commissao', 'Programa': 'nome_programa', 'Área de Concentração': 'area_concentracao'
        }[tipo_filtro]
        
        df_resultado = df[df[coluna_df] == item_selecionado]
        
        if not df_resultado.empty:
            # Preparar dados para editor
            cols = ['codigo', 'disciplina', 'n_creditos']
            df_selecao = df_resultado[cols].copy().reset_index(drop=True)
            df_selecao['Selecionar'] = df_selecao['codigo'].apply(lambda x: x in st.session_state.selecionadas)
            df_selecao = df_selecao[['Selecionar'] + cols]

            st.markdown("### 2. Seleção de Disciplinas")
            st.data_editor(
                df_selecao,
                hide_index=True,
                use_container_width=True,
                column_config={"Selecionar": st.column_config.CheckboxColumn("Selecionar", width="small")},
                key="editor_disciplinas",
                on_change=atualizar_selecao,
                args=(df_selecao,)
            )
        else:
            st.warning("Nenhuma disciplina encontrada para este filtro.")

    # --- ÁREA DE CRÉDITOS (RESTORED) ---
    st.divider()
    st.markdown("### 3. Resumo de Créditos")
    
    df_sel_total = df[df['codigo'].isin(st.session_state.selecionadas)]
    soma_total = df_sel_total['n_creditos'].sum()
    soma_obrig = df_sel_total[df_sel_total['codigo'].isin(obrigatorias)]['n_creditos'].sum()

    # Métricas e Barras
    c1, c2 = st.columns(2)
    with c1:
        st.metric(f"Créditos Totais (Meta: {creditos_necessarios})", f"{soma_total}")
        prog_total = min(soma_total / creditos_necessarios, 1.0) if creditos_necessarios > 0 else 0
        st.progress(prog_total)
        
    with c2:
        st.metric(f"Créditos Obrigatórios (Meta: {creditos_obrigatorios})", f"{soma_obrig}")
        prog_obrig = min(soma_obrig / creditos_obrigatorios, 1.0) if creditos_obrigatorios > 0 else 0
        st.progress(prog_obrig)

    # --- VALIDAÇÕES DE STATUS (RESTORED) ---
    st.subheader("Status das Metas")
    
    # 1. Check de Créditos Obrigatórios
    if soma_obrig >= creditos_obrigatorios:
        st.success(f"✔ Meta de Obrigatórias Atingida! ({soma_obrig}/{creditos_obrigatorios})")
    else:
        st.warning(f"✖ Faltam {creditos_obrigatorios - soma_obrig} créditos obrigatórios.")

    # 2. Check de Créditos Totais
    if soma_total >= creditos_necessarios:
        st.success(f"✔ Meta de Créditos Totais Atingida! ({soma_total}/{creditos_necessarios})")
    else:
        st.warning(f"✖ Faltam {creditos_necessarios - soma_total} créditos totais.")


    # --- LISTA DE DISCIPLINAS SELECIONADAS ---
    if not df_sel_total.empty:
        with st.expander(f"Ver lista das {len(df_sel_total)} disciplinas selecionadas"):
            st.dataframe(df_sel_total[['codigo', 'disciplina', 'n_creditos']], hide_index=True, use_container_width=True)
            
            # Botão Limpar
            if st.button("Limpar Todas as Seleções"):
                st.session_state.selecionadas.clear()
                st.rerun()

    # --- ÁREA DO GRAFO (CORRIGIDA) ---
    st.divider()
    st.markdown("### 4. Visualização de Rede (Docentes x Disciplinas)")
    
    with st.expander("🕸️ Ver Grafo Interativo do Filtro Atual", expanded=True):
        if df_resultado.empty:
            st.info("Utilize os filtros no topo da página (Passo 1) para gerar o grafo de conexões.")
        else:
            st.caption("**Legenda:** 🟣 Círculos = Disciplinas (Cores = Comunidades) | ♦️ Losangos Cinzas = Docentes")
            renderizar_grafo_interativo(df_resultado)