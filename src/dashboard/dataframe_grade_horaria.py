import pandas as pd
from pathlib import Path
from typing import List
from utils.config.subjects import obrigatorias
import networkx as nx


def gerar_dataset_dashboard(
    output_pickle_path: Path,
    community_pickle_path: Path,
    institutos_alvo: List[str] = None
) -> pd.DataFrame:
    """
    Gera o dataset final para o dashboard:
    1. Unifica dados brutos e comunidades.
    2. Marca disciplinas obrigatórias.
    3. Filtra por instituto.

    Args:
        output_pickle_path: Path do output.pickle.
        community_pickle_path: Path do community.pickle.
        institutos_alvo: Lista de institutos para filtrar.
    """
    
    # --- Configuração Padrão ---
    if institutos_alvo is None:
        institutos_alvo = [
            "Instituto de Ciências Matemáticas e de Computação",
            "Instituto de Matemática, Estatística e Ciência da Computação"
        ]

    # --- Carregamento ---
    if not output_pickle_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {output_pickle_path}")
    
    if not community_pickle_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {community_pickle_path}")

    print("Carregando datasets...")
    df_main = pd.read_pickle(output_pickle_path)
    df_comm = pd.read_pickle(community_pickle_path)

    # --- Tratamento de Chaves ---
    df_main['codigo'] = df_main['codigo'].astype(str).str.strip()
    
    df_comm['codigo'] = df_comm['codigo'].astype(str).str.strip()

    # --- Etapa 1: Merge (Comunidades) ---
    print("Unindo dados de comunidade...")
    df_merged = pd.merge(df_main, df_comm, on=['codigo', 'disciplina'], how='left')

    # --- Etapa 2: Identificar Obrigatórias ---
    print(f"Identificando disciplinas obrigatórias ({len(obrigatorias)} listadas)...")
    
    # Cria a coluna 'eh_obrigatoria' (True/False)
    # .isin é muito rápido e eficiente para isso
    df_merged['eh_obrigatoria'] = df_merged['codigo'].isin(obrigatorias)
    df_merged.head(10)

    # --- Etapa 3: Filtragem por Instituto ---
    print(f"Filtrando por comissao: {institutos_alvo}")
    df_final = df_merged[df_merged['commissao'].isin(institutos_alvo)].copy()

    # --- Resumo Final ---
    n_total = len(df_final)
    n_obrig = df_final['eh_obrigatoria'].sum()
    print(f"--- Processamento Concluído ---")
    print(f"Total de disciplinas: {n_total}")
    print(f"Disciplinas obrigatórias encontradas neste filtro: {n_obrig}")
    
    return df_final

def construir_grafo_docentes_enrichido(df: pd.DataFrame) -> nx.Graph:
    """
    Constrói um grafo bipartido (Docentes x Disciplinas) enriquecido com metadados.
    """
    G = nx.Graph()
    
    print(f"Iniciando construção do grafo com {len(df)} disciplinas...")

    for _, row in df.iterrows():
        # --- A. Nó da Disciplina ---
        # Adicionamos todos os atributos úteis para visualização posterior (Gephi/Streamlit)
        node_id = str(row['codigo']).strip()
        
        # Tratamento de NaNs para metadados
        comunidade = int(row['community']) if pd.notna(row.get('community')) else -1
        eh_obrigatoria = bool(row['eh_obrigatoria']) if 'eh_obrigatoria' in df.columns else False
        instituto = str(row['commissao']) if pd.notna(row.get('commissao')) else "Desconhecido"

        G.add_node(
            node_id,
            label=row['disciplina'],
            bipartite=0,          # 0 = Disciplina
            type='disciplina',
            community=comunidade,
            is_mandatory=eh_obrigatoria,
            institute=instituto
        )

        # --- B. Nós dos Docentes e Arestas ---
        raw_docentes = row.get('docentes_responsaveis')
        
        if pd.isna(raw_docentes) or str(raw_docentes).strip() == '':
            continue

        # Separa por pipe '|' e remove espaços
        lista_docentes = [d.strip() for d in str(raw_docentes).split('|')]

        for docente in lista_docentes:
            if not docente: continue

            # Adiciona Nó do Docente (se já existir, o networkx apenas atualiza/ignora)
            G.add_node(
                docente,
                label=docente,
                bipartite=1,      # 1 = Docente
                type='docente'
            )

            # Cria a conexão Disciplina <-> Docente
            G.add_edge(node_id, docente)

    print(f"Grafo construído com sucesso!")
    print(f"Nós: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}")
    return G

def enriquecer_grafo_disciplinas(
    path_grafo_original: Path,
    df_metadados: pd.DataFrame
) -> nx.Graph:
    """
    Carrega o grafo k-NN original, filtra para manter apenas as disciplinas
    do escopo (ICMC/IME) e adiciona metadados (comunidade, obrigatória).
    """
    
    if not path_grafo_original.exists():
        raise FileNotFoundError(f"Grafo original não encontrado em: {path_grafo_original}")

    print(f"Carregando grafo original de {path_grafo_original}...")
    G = nx.read_graphml(path_grafo_original)
    
    print(f"Tamanho Original: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas.")

    # --- 1. Preparar Lista de Nós Válidos ---
    # Criamos um set dos códigos que estão no DataFrame já filtrado (ICMC/IME)
    codigos_validos = set(df_metadados['codigo'].astype(str).str.strip())

    # --- 2. Filtragem dos Nós ---
    # Identifica nós que NÃO estão no dataframe filtrado
    nos_para_remover = [n for n in G.nodes() if str(n).strip() not in codigos_validos]
    
    if nos_para_remover:
        print(f"Removendo {len(nos_para_remover)} nós fora do escopo (outros institutos)...")
        G.remove_nodes_from(nos_para_remover)
    
    # --- 3. Enriquecimento dos Nós Restantes ---
    print("Atualizando metadados dos nós...")
    
    # Transforma o DF em um dicionário indexado pelo código para acesso rápido
    df_indexed = df_metadados.set_index('codigo')

    for node_id in G.nodes():
        # Garante chave limpa
        clean_id = str(node_id).strip()
        
        if clean_id in df_indexed.index:
            row = df_indexed.loc[clean_id]
            
            # Atualiza/Sobrescreve atributos do nó
            # O NetworkX permite adicionar atributos arbitrários
            G.nodes[node_id]['label'] = str(row['disciplina'])
            G.nodes[node_id]['community'] = int(row['community']) if pd.notna(row.get('community')) else -1
            G.nodes[node_id]['is_mandatory'] = bool(row['eh_obrigatoria'])
            G.nodes[node_id]['institute'] = str(row['commissao'])
            G.nodes[node_id]['n_creditos'] = int(row['n_creditos']) if pd.notna(row.get('n_creditos')) else 0
            
            # Tag de tipo para diferenciar no futuro se misturar grafos
            G.nodes[node_id]['type'] = 'disciplina'

    print(f"Grafo Final: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas.")
    return G

if __name__ == "__main__":
    # --- Caminhos de Entrada ---
    PATH_OUTPUT = Path(r'src\data\output.pickle')
    PATH_COMMUNITY = Path(r'src\data\community.pickle')
    PATH_GRAPH_ORIGINAL = Path(r'src\data\graph.graphml') # O arquivo que você mencionou
    
    # --- Caminho de Saída ---
    # Salvamos na pasta grade_horaria, pronto para o dashboard ler
    PATH_GRAPH_FINAL = Path(r"src\data\grade_horaria\grafo_disciplinas_enrichido.graphml")

    try:
        # 1. Gera o DataFrame Mestre (Filtrado e com Obrigatórias)
        print("--- Passo 1: Carregando Metadados ---")
        df_completo = gerar_dataset_dashboard(PATH_OUTPUT, PATH_COMMUNITY)

        # 2. Processa o Grafo
        print("\n--- Passo 2: Processando Grafo ---")
        G_final = enriquecer_grafo_disciplinas(PATH_GRAPH_ORIGINAL, df_completo)

        # 3. Salva
        print("\n--- Passo 3: Salvando ---")
        PATH_GRAPH_FINAL.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(G_final, PATH_GRAPH_FINAL)
        print(f"✅ Grafo de disciplinas salvo em: {PATH_GRAPH_FINAL}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()