"""
Página para selecionar disciplinas por categoria e calcular créditos.
As seleções são persistentes entre mudanças de filtro.
"""

import pandas as pd
import streamlit as st
from pathlib import Path
from utils.config.subjects import obrigatorias, creditos_necessarios, creditos_obrigatorios

# Simula o caminho do arquivo de dados
DATA_PATH = Path('src/data/output.pickle')

@st.cache_data
def get_data() -> pd.DataFrame:
    """
    Carrega os dados do arquivo pickle.
    """
    if not DATA_PATH.exists():
        st.error(f"Arquivo de dados não encontrado em: {DATA_PATH}")
        # Retorna um DataFrame vazio com as colunas esperadas para evitar mais erros
        return pd.DataFrame(columns=[
            'commissao', 'nome_programa', 'area_concentracao', 
            'codigo', 'disciplina', 'n_creditos'
        ])
    try:
        return pd.read_pickle(DATA_PATH)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=[
            'commissao', 'nome_programa', 'area_concentracao', 
            'codigo', 'disciplina', 'n_creditos'
        ])

# --- Fim dos Mocks ---


def setup_new_filters(df):
    """
    Cria os filtros de seleção única (Categoria -> Item).
    """
    st.subheader("Filtro de Disciplinas")
    col1, col2 = st.columns(2)

    # Dicionário para mapear a escolha para a coluna real no DataFrame
    mapa_filtro = {
        'Comissão': 'commissao',
        'Programa': 'nome_programa',
        'Área de Concentração': 'area_concentracao'
    }

    # Seletor 1: Escolher o TIPO de filtro
    with col1:
        tipo_filtro = st.selectbox(
            "1. Filtrar por:",
            options=['Selecione um tipo', 'Comissão', 'Programa', 'Área de Concentração']
        )
    
    item_selecionado = None
    
    # Seletor 2: Escolher o ITEM (baseado no tipo)
    with col2:
        if tipo_filtro == 'Selecione um tipo':
            st.selectbox(
                "2. Selecione o item:",
                options=['--'],
                disabled=True
            )
        else:
            # Pega o nome da coluna correta
            coluna_df = mapa_filtro[tipo_filtro]
            
            # Pega as opções únicas e ordenadas
            opcoes = sorted(df[coluna_df].unique())
            
            item_selecionado = st.selectbox(
                f"2. Selecione o {tipo_filtro}:",
                options=['Selecione'] + opcoes
            )
            
    return tipo_filtro, item_selecionado


# --- Configuração da Página ---

st.set_page_config(layout="wide", page_title="Selecionar Disciplinas")

# 1. INICIALIZA O SESSION STATE
# Usamos um set() para guardar os códigos das disciplinas selecionadas
if 'selecionadas' not in st.session_state:
    st.session_state.selecionadas = set()

st.title("Seletor de Disciplinas da Pós-Graduação")
st.markdown(
    "Use os filtros para encontrar as disciplinas e clique nas caixas "
    "de seleção. O total de créditos será calculado abaixo."
)

df = get_data()

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique o console para mais detalhes.")
else:
    
    # --- INÍCIO DA CORREÇÃO ---
    # 1. Define a função de callback que fará a lógica de atualização.
    def atualizar_selecao(df_tabela_atual):
        """
        Callback para atualizar o session_state diretamente com base
        nas edições feitas no st.data_editor.
        """
        # Acessa o dicionário de edições (a fonte da verdade)
        # Verifica se a key existe antes de acessá-la
        if "editor_disciplinas" not in st.session_state:
            return
            
        edicoes = st.session_state["editor_disciplinas"]
        
        # Itera sobre as linhas que foram editadas
        for index_editado, edicao in edicoes.get('edited_rows', {}).items():
            # Verifica se a coluna 'Selecionar' foi a que mudou
            if 'Selecionar' in edicao:
                # Pega o código da disciplina usando o índice do dataframe original
                # que foi passado para o editor
                try:
                    codigo = df_tabela_atual.iloc[index_editado]['codigo']
                except IndexError:
                    # Pode acontecer se o dataframe for filtrado rapidamente
                    continue 
                    
                # Atualiza o set principal no session_state
                if edicao['Selecionar'] is True:
                    st.session_state.selecionadas.add(codigo)
                elif edicao['Selecionar'] is False:
                    st.session_state.selecionadas.discard(codigo) # Usar discard é mais seguro que remove
    # --- FIM DA CORREÇÃO ---

    tipo_filtro, item_selecionado = setup_new_filters(df)
    
    st.header("Resultados da Filtragem")

    # Verifica se o usuário selecionou um item válido
    if item_selecionado and item_selecionado != 'Selecione':
        
        # Filtra o DataFrame com base na escolha
        coluna_df = {
            'Comissão': 'commissao',
            'Programa': 'nome_programa',
            'Área de Concentração': 'area_concentracao'
        }[tipo_filtro]
        
        df_resultado = df[df[coluna_df] == item_selecionado]
        
        if df_resultado.empty:
            st.warning("Nenhuma disciplina encontrada para o item selecionado.")
        else:
            # Prepara o DataFrame para o data_editor
            df_selecao = df_resultado[
                ['codigo', 'disciplina', 'n_creditos']
            ].copy().reset_index(drop=True) # Reseta o index para garantir que iloc[index_editado] funcione
            
            # ADICIONA A COLUNA 'Selecionar'
            df_selecao['Selecionar'] = df_selecao['codigo'].apply(
                lambda x: x in st.session_state.selecionadas
            )
            
            # Reordena colunas para 'Selecionar' vir primeiro
            df_selecao = df_selecao[['Selecionar', 'codigo', 'disciplina', 'n_creditos']]

            # Usa st.data_editor para criar a tabela interativa
            st.data_editor(
                df_selecao,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Selecionar": st.column_config.CheckboxColumn(
                        "Selecionar", 
                        help="Marque para somar os créditos."
                    ),
                    "codigo": "Código",
                    "disciplina": "Disciplina",
                    "n_creditos": "Créditos",
                },
                # --- APLICAÇÃO DA CORREÇÃO ---
                key="editor_disciplinas",  # Chave única para o editor
                on_change=atualizar_selecao, # Define a função de callback
                args=(df_selecao,) # Passa o dataframe filtrado para o callback
                # --- FIM DA APLICAÇÃO ---
            )
            
    else:
        st.info(
            "Por favor, selecione um **Tipo de Filtro** e um **Item** "
            "para exibir as disciplinas."
        )

    # 4. DASHBOARD DE CRÉDITOS (SEMPRE VISÍVEL)
    st.divider()
    st.header("Resumo Total dos Créditos")
    
    soma_total = 0
    soma_obrigatorias = 0
    df_total_selecionado = pd.DataFrame(columns=['codigo', 'disciplina', 'n_creditos']) # Inicializa vazio
    
    if not st.session_state.selecionadas:
        st.info("Nenhuma disciplina selecionada.")
    else:
        # Filtra o DataFrame *completo* (df) com base em TUDO que está no session_state
        df_total_selecionado = df[df['codigo'].isin(st.session_state.selecionadas)]
        soma_total = df_total_selecionado['n_creditos'].sum()

        # --- INÍCIO DA NOVA LÓGICA ---
        # Filtra as selecionadas para achar as obrigatórias
        df_obrigatorias_selecionadas = df_total_selecionado[
            df_total_selecionado['codigo'].isin(obrigatorias)
        ]
        soma_obrigatorias = df_obrigatorias_selecionadas['n_creditos'].sum()
        # --- FIM DA NOVA LÓGICA ---

    # Exibe as métricas lado a lado
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            f"Créditos Totais (Meta: {creditos_necessarios})", 
            value=f"{soma_total} / {creditos_necessarios}"
        )
    with col2:
        st.metric(
            f"Créditos Obrigatórios (Meta: {creditos_obrigatorios})", 
            value=f"{soma_obrigatorias} / {creditos_obrigatorios}"
        )

    # Barras de Progresso
    progresso_total = 0.0
    if creditos_necessarios > 0: # Evita divisão por zero
        progresso_total = min(soma_total / creditos_necessarios, 1.0)
        
    st.progress(progresso_total, text=f"{(progresso_total * 100):.1f}% da meta total atingida")

    progresso_obrigatorias = 0.0
    if creditos_obrigatorios > 0: # Evita divisão por zero
        progresso_obrigatorias = min(soma_obrigatorias / creditos_obrigatorios, 1.0)

    st.progress(progresso_obrigatorias, text=f"{(progresso_obrigatorias * 100):.1f}% da meta obrigatória atingida")

    # 5. COMPARAÇÃO (COM SEÇÃO SEPARADA PARA OBRIGATÓRIAS)
    st.subheader("Status das Metas")
    
    # Check de Créditos Obrigatórios
    if soma_obrigatorias >= creditos_obrigatorios:
        st.success(f"✔ Parabéns! Você atingiu a meta de {creditos_obrigatorios} créditos obrigatórios.")
    else:
        st.warning(f"✖ Faltam {creditos_obrigatorios - soma_obrigatorias} créditos obrigatórios.")

    # Check de Créditos Totais
    if soma_total >= creditos_necessarios:
        st.success(f"✔ Parabéns! Você atingiu a meta de {creditos_necessarios} créditos totais.")
    else:
        st.warning(f"✖ Faltam {creditos_necessarios - soma_total} créditos totais.")


    # LISTA DE DISCIPLINAS
    st.subheader("Disciplinas Selecionadas")
    with st.expander(f"Mostrar as {len(df_total_selecionado)} disciplinas selecionadas..."):
        if df_total_selecionado.empty:
            st.write("Nenhuma disciplina selecionada.")
        else:
            # Prepara o DF para exibição, adicionando a coluna de status
            df_display = df_total_selecionado[['codigo', 'disciplina', 'n_creditos']].copy()
            df_display['Status'] = df_display['codigo'].apply(
                lambda x: 'Obrigatória' if x in obrigatorias else 'Opcional'
            )
            df_display = df_display[['codigo', 'disciplina', 'n_creditos', 'Status']] # Reordena

            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True
            )

    # Botão para limpar a seleção
    if st.button("Limpar todas as seleções", use_container_width=True):
        st.session_state.selecionadas.clear()
        st.rerun()