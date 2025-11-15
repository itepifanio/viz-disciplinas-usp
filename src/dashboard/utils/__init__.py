from pathlib import Path

import pandas as pd
import streamlit as st

from utils.config import scrapper_data_path, preprocessed_data_path
from utils.data_reader import DataReader

@st.cache_data
def get_data() -> pd.DataFrame:
    """
    Read scrapped data and preprocess its values.
    """
    return DataReader(scrapper_data_path, preprocessed_data_path).dataframe


def num_docentes(series_docentes: pd.Series) -> int:
    docentes_unicos = set()
    
    for lista_docentes in series_docentes:
        docentes = [
            d.strip() for d in lista_docentes.split('|') 
            if d.strip()
        ]
        docentes_unicos.update(docentes)
        
    return len(docentes_unicos)

def filter_data(
    df: pd.DataFrame, 
    comissao: str, 
    programa: str, 
    area: str, 
    busca: str
) -> pd.DataFrame:
    """
    Aplica filtros selecionados a um DataFrame.
    'Todas' ou 'Todos' são usados como valores para ignorar um filtro.
    """
    df_resultado = df.copy()

    if comissao and comissao != 'Todas':
        df_resultado = df_resultado[df_resultado['commissao'] == comissao]
        
    if programa and programa != 'Todos':
        df_resultado = df_resultado[df_resultado['nome_programa'] == programa]

    if area and area != 'Todas':
        df_resultado = df_resultado[df_resultado['area_concentracao'] == area]

    if busca:
        df_resultado = df_resultado[df_resultado['disciplina'].str.contains(busca, case=False, na=False)]
        
    return df_resultado
