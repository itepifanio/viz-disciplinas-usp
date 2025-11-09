import streamlit as st
import pandas as pd
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt

# --- Configuração da Página ---
# Isso deve ser o primeiro comando Streamlit no seu script
st.set_page_config(
    page_title="Meu Dashboard de Dados",
    layout="wide"
)

# --- Carregamento de Dados ---
# Usamos @st.cache_data para que o Streamlit não recarregue o arquivo 
# toda vez que o usuário interagir com o dashboard.
@st.cache_data
def load_data(pickle_path):
    """Carrega o DataFrame a partir de um arquivo pickle."""
    scrap_file = Path(pickle_path)
    
    if not scrap_file.exists():
        # Exibe uma mensagem de erro no dashboard se o arquivo não for encontrado
        st.error(f"Arquivo não encontrado em: {scrap_file.resolve()}")
        return pd.DataFrame()  # Retorna um DataFrame vazio
        
    try:
        df = pd.read_pickle(scrap_file)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo pickle: {e}")
        return pd.DataFrame()

# --- Título do Dashboard ---
st.title("Dashboard de Análise de Dados")

# --- Carregar e Exibir os Dados ---
# Defina o caminho para o seu arquivo
FILE_PATH = r'..\nbs\output.pickle' 
df = load_data(FILE_PATH)

if not df.empty:
    st.header("Visualização dos Dados Carregados")
    st.write("Abaixo está uma amostra dos seus dados:")
    
    # st.dataframe exibe um DataFrame interativo
    st.dataframe(df.head())
    
    st.info(f"Total de {len(df)} linhas carregadas.")

    # --- Adicionar um exemplo de interatividade ---
    st.header("Exploração de Colunas")
    
    # Permite ao usuário selecionar uma coluna para ver mais detalhes
    all_columns = df.columns.tolist()
    column_to_inspect = st.selectbox("Selecione uma coluna para inspecionar:", all_columns)
    
    if column_to_inspect:
        st.write(f"**Valores Únicos na coluna '{column_to_inspect}':**")
        st.write(df[column_to_inspect].unique())
        
        st.write(f"**Contagem de valores (Top 10):**")
        st.bar_chart(df[column_to_inspect].value_counts().head(10))

else:
    st.warning("Não foi possível carregar os dados. Verifique o caminho do arquivo.")

# --- Barra Lateral (Sidebar) ---
st.sidebar.header("Sobre")
st.sidebar.info("Este é um dashboard de exemplo criado com Streamlit para exibir dados de um arquivo pickle.")