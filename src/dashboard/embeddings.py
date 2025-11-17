import streamlit as st

import pandas as pd
import plotly.express as px

from utils.config.path import umap_data_path, tsne_data_path

@st.cache_data
def get_data(path: str) -> pd.DataFrame:
    return pd.read_pickle(path)

def embedding_plot(
    title: str,
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = 'commissao',
) -> px.scatter:
    ordered_col = sorted(df[color_col].unique())
    cat_order_dict = {color_col: ordered_col}

    return px.scatter(
        df,
        x=x_col,
        y=y_col,
        template="plotly_white",
        category_orders=cat_order_dict,
        hover_data=df.columns.tolist(),
        color=color_col,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Alphabet,
    )

st.plotly_chart(
    embedding_plot(
        title="UMAP Embeddings",
        df=get_data(umap_data_path),
        x_col='umap_x',
        y_col='umap_y',
    )
)

st.plotly_chart(
    embedding_plot(
        title="t-SNE Embeddings",
        df=get_data(tsne_data_path),
        x_col='tsne_x',
        y_col='tsne_y',
    )
)
