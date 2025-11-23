# %%
import pandas as pd
from pathlib import Path
import networkx as nx
# %%

df_path = Path('src\data\grade_horaria\dados_dashboard_completo.pickle')
df = pd.read_pickle(df_path)
# %%
print(df[df['codigo']=='SMA5996'][['docentes_responsaveis', 'disciplina', 'codigo', 'carga_total', 'n_creditos']])
print(df.columns)

# %%
graph_path = Path('src\data\grade_horaria\grafo_disciplinas_enrichido.graphml')
G = nx.read_graphml(graph_path)
# %%
print(G.nodes['SMA5996'])
