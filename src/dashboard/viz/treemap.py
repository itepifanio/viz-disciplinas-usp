import pandas as pd

import plotly.express as px

def treemap(df: pd.DataFrame, col: str) -> px.treemap:
    """
    Create a treemap visualization from the given DataFrame.

    Parameters:
    df: DataFrame containing the data for the treemap. 
        It should have columns 'commissao', 'area_concentracao', and 'disciplina'.

    Returns:
    px.treemap: A Plotly treemap figure.
    """
    return px.treemap(
        df,
        path=['commissao', 'area_concentracao', 'disciplina'],
        values=col,
        color_continuous_scale='Viridis',
        title='Treemap Visualization'
    )
