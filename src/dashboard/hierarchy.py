from viz.treemap import treemap

from utils import get_data

import streamlit as st

data_mapping = {
    "n_creditos": "Nº Créditos",
    "carga_teorica": "Carga Teórica (por semana)",
    "carga_pratica": "Carga Prática (por semana)",
    "carga_estudo": "Carga de Estudo (por semana)",
    "duracao": "Duração total (em horas)",
    "carga_total": "Carga Total (em horas)",
}

def format_display_name(option_key: str):
    return data_mapping.get(option_key, option_key)

col_filter = st.selectbox(
    'Selecione a métrica de carga horária a ser analisada:',
    options=list(data_mapping.keys()),
    format_func=format_display_name,
    index=len(data_mapping) - 1,
    help='Selecione o valor que determinará o tamanho dos retângulos no treemap.'
)

st.plotly_chart(
    treemap(get_data(), col=str(col_filter))
)
