"""
Página para explorar a lista de disciplinas de Pós-Graduação.
"""

import pandas as pd
import streamlit as st

# Importa as funções partilhadas do nosso módulo de utilitários
from utils import get_data, num_docentes, filter_data

def setup_filters(df):
    """
    Cria os filtros no corpo principal da página e retorna as seleções.
    """
    st.subheader("Filtros da Hierarquia")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
    
    # Nível 1: Comissão de Pós-Graduação
    comissoes = sorted(df['commissao'].unique())
    lista_comissoes = ['Todas'] + comissoes
    comissao_selecionada = col1.selectbox(
        "1. Comissão de Pós-Graduação",
        lista_comissoes,
        help="Selecione a comissão de pós-graduação para filtrar os programas."
    )
    
    # Nível 2: Programa (dependente do Nível 1)
    if comissao_selecionada == 'Todas':
        df_filtrado_comissao = df
    else:
        df_filtrado_comissao = df[df['commissao'] == comissao_selecionada]
        
    programas = sorted(df_filtrado_comissao['nome_programa'].unique())
    lista_programas = ['Todos'] + programas
    programa_selecionado = col2.selectbox(
        "2. Programa",
        lista_programas,
        help="Selecione o programa para filtrar as áreas de concentração."
    )
    
    # Nível 3: Área de Concentração (dependente do Nível 2)
    if programa_selecionado == 'Todos':
        df_filtrado_programa = df_filtrado_comissao
    else:
        df_filtrado_programa = df_filtrado_comissao[df_filtrado_comissao['nome_programa'] == programa_selecionado]
        
    areas = sorted(df_filtrado_programa['area_concentracao'].unique())
    lista_areas = ['Todas'] + areas
    area_selecionada = col3.selectbox(
        "3. Área de Concentração",
        lista_areas,
        help="Selecione a área de concentração para filtrar as disciplinas."
    )
    
    # Nível 4: Disciplina (Busca textual)
    busca_disciplina = col4.text_input(
        "4. Buscar Disciplina por Nome",
        help="Digite parte do nome de uma disciplina para buscar (opcional)."
    )
    
    return comissao_selecionada, programa_selecionado, area_selecionada, busca_disciplina

st.set_page_config(layout="wide", page_title="Disciplinas de Pós-Graduação")

st.title("Explorador de Disciplinas da Pós-Graduação")

df = get_data()

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique a configuração e o ficheiro de dados.")
else:
    comissao, programa, area, busca = setup_filters(df)
    
    st.header("Resultados")

    all_filters_selected = (
        comissao != 'Todas' and
        programa != 'Todos' and
        area != 'Todas'
    )
    
    if all_filters_selected:
        df_resultado = filter_data(df, comissao, programa, area, busca)
        st.dataframe(
            df_resultado,
            column_config={
                "codigo": "Código",
                "disciplina": "Disciplina",
                "n_creditos": "Nº Créditos",
                "carga_teorica": "Carga Teórica",
                "carga_pratica": "Carga Prática",
                "carga_estudo": "Carga de Estudo",
                "carga_total": "Carga Total",
                "docentes": "Docentes",
            }
        )
    else:
        st.info(
            "Por favor, selecione uma **Comissão de Pós-Graduação**, "
            "um **Programa** e uma **Área de Concentração** "
            "para exibir as disciplinas."
        )
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Disciplinas Filtradas", 0)
        with col2:
            st.metric("Total de Docentes Únicos", 0)
