import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
import umap.umap_ as umap
import re
from pathlib import Path
import sys
import networkx as nx
from sklearn.neighbors import NearestNeighbors

# --- 1. Configuração de Stopwords (Multi-idioma) ---
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Baixando stopwords (pt e en) do NLTK...")
    nltk.download('stopwords')

# Combinamos stopwords em português e inglês em um único conjunto
stop_words_pt = set(stopwords.words('portuguese'))
stop_words_en = set(stopwords.words('english'))
stop_words_global = stop_words_pt.union(stop_words_en)
print(f"Stopwords carregadas: {len(stop_words_global)} palavras (PT+EN).")

# --- 2. Funções Helper (Limpeza e Modelagem) ---

def limpar_e_remover_stopwords(texto: str) -> str:
    """
    Limpa um texto: minúsculas, remove pontuação/números, 
    remove stopwords (PT e EN).
    """
    if not isinstance(texto, str):
        return "" 
    
    texto = texto.lower()
    texto = re.sub(r'[^a-z\s]', '', texto) 
    
    palavras = [
        palavra for palavra in texto.split() 
        if palavra not in stop_words_global and len(palavra) > 2
    ]
    
    return ' '.join(palavras)

def gerar_embeddings(textos: list, nome_modelo: str) -> np.ndarray:
    """
    Carrega um modelo e gera embeddings a partir de uma lista de textos.
    Retorna uma matriz NumPy.
    """
    print(f"Carregando o modelo '{nome_modelo}'...")
    try:
        model = SentenceTransformer(nome_modelo)
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}", file=sys.stderr)
        return np.array([])
    
    print(f"Gerando embeddings para {len(textos)} textos...")
    embeddings = model.encode(textos, show_progress_bar=True)
    print("Geração de embeddings concluída.")
    return embeddings

def aplicar_umap(embeddings: np.ndarray) -> np.ndarray:
    """
    Aplica UMAP (2D) a uma matriz de embeddings.
    """
    print("Aplicando UMAP para redução de dimensionalidade (2D)...")
    reducer = umap.UMAP(
        n_neighbors=15, min_dist=0.1, n_components=2, 
        metric='cosine', random_state=42
    )
    embedding_2d = reducer.fit_transform(embeddings)
    print("UMAP concluído.")
    return embedding_2d

def construir_grafo_knn(
    embeddings: np.ndarray, 
    node_ids: list, 
    node_labels: list, 
    k: int = 3
) -> nx.Graph:
    """
    Constrói um grafo NetworkX conectando os k-vizinhos mais próximos
    com base nos embeddings.
    """
    print(f"Construindo grafo k-NN (k={k})...")
    
    # Configuramos o NearestNeighbors para encontrar k+1 vizinhos
    # (pois o primeiro vizinho é sempre o próprio ponto)
    nn = NearestNeighbors(n_neighbors=k + 1, metric='cosine', algorithm='brute')
    nn.fit(embeddings)
    
    # Obtemos os índices dos vizinhos para cada ponto
    # Não precisamos das distâncias, apenas dos índices
    indices = nn.kneighbors(embeddings, return_distance=False)
    
    G = nx.Graph()
    
    print("Adicionando nós ao grafo...")
    # Adiciona todos os nós primeiro, com seus metadados (labels)
    for i, node_id in enumerate(node_ids):
        G.add_node(node_id, label=node_labels[i])
        
    print("Adicionando arestas k-NN ao grafo...")
    # Adiciona as arestas
    for i, neighbors in enumerate(indices):
        origem_id = node_ids[i]
        
        # Iteramos de 1 a k (pulamos o 0, que é o self-loop)
        for j in range(1, k + 1): 
            vizinho_idx = neighbors[j]
            vizinho_id = node_ids[vizinho_idx]
            
            # Adicionamos a aresta (o Grafo lida com duplicatas)
            G.add_edge(origem_id, vizinho_id)
            
    print(f"Grafo construído: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas.")
    return G

# --- 3. Função Principal do Pipeline ---

def processar_artefatos_disciplinas(
    df_original: pd.DataFrame, 
    colunas_texto: list, 
    coluna_codigo: str, 
    coluna_disciplina: str, 
    nome_modelo: str,
    path_saida_umap: Path,
    path_saida_grafo: Path
):
    """
    Executa o pipeline completo:
    1. Limpa e concatena textos.
    2. Gera embeddings.
    3. Aplica UMAP -> Salva Artefato 1 (Pickle).
    4. Constrói Grafo k-NN -> Salva Artefato 2 (GraphML).
    """
    
    print("--- Iniciando pipeline de processamento ---")
    
    # --- Passo 1: Limpar e Concatenar Textos ---
    print(f"Limpando e concatenando as colunas: {', '.join(colunas_texto)}")
    df_proc = df_original.copy()
    
    colunas_limpas = []
    for col in colunas_texto:
        col_limpa = f"{col}_limpa"
        df_proc[col_limpa] = df_proc[col].apply(limpar_e_remover_stopwords)
        colunas_limpas.append(col_limpa)
    
    textos_para_embeddar = df_proc[colunas_limpas].apply(
        lambda row: ' '.join(row.astype(str)), 
        axis=1
    ).fillna('').tolist()

    # --- Passo 2: Gerar Embeddings ---
    matrix_embeddings = gerar_embeddings(textos_para_embeddar, nome_modelo)
    
    if matrix_embeddings.size == 0:
        print("Falha na geração de embeddings. Abortando.", file=sys.stderr)
        return

    # --- Passo 3: Artefato 1 - UMAP ---
    embedding_2d = aplicar_umap(matrix_embeddings)
    
    print(f"Montando DataFrame UMAP...")
    df_umap = pd.DataFrame({
        coluna_codigo: df_original[coluna_codigo],
        coluna_disciplina: df_original[coluna_disciplina],
        'umap_x': embedding_2d[:, 0],
        'umap_y': embedding_2d[:, 1]
    })
    
    # Salvar Artefato 1
    df_umap.to_pickle(path_saida_umap)
    print(f"✅ Artefato UMAP salvo em: {path_saida_umap.resolve()}")
    print("\nAmostra do DataFrame UMAP:")
    print(df_umap.head())

    # --- Passo 4: Artefato 2 - Grafo k-NN ---
    # Precisamos das listas de 'codigo' e 'disciplina' para os nós
    lista_codigos = df_original[coluna_codigo].tolist()
    lista_disciplinas = df_original[coluna_disciplina].tolist()
    
    G = construir_grafo_knn(
        embeddings=matrix_embeddings,
        node_ids=lista_codigos,
        node_labels=lista_disciplinas,
        k=3 # Conforme solicitado: 3 vizinhos mais próximos
    )
    
    # Salvar Artefato 2
    # Usamos GraphML por ser um formato padrão e legível
    nx.write_graphml(G, path_saida_grafo)
    print(f"✅ Artefato Grafo salvo em: {path_saida_grafo.resolve()}")

    print("\n--- Pipeline concluído com sucesso ---")
    print("Dois arquivos foram gerados para o seu dashboard.")

# --- 4. Bloco de Execução ---

if __name__ == '__main__':
    
    # --- PARÂMETROS DE ENTRADA ---
    ARQUIVO_DADOS_BRUTOS = Path(r'..\nbs\output.pickle')
    
    # Nomes dos arquivos de saída (os artefatos)
    ARQUIVO_SAIDA_UMAP = Path('dados_umap_para_streamlit.pickle')
    ARQUIVO_SAIDA_GRAFO = Path('grafo_disciplinas.graphml')
    
    COLUNAS_TEXTO = ['objetivos', 'justificativa', 'conteudo']
    
    # ATENÇÃO: Verifique se 'disciplina' é o nome correto da coluna
    COLUNA_CODIGO = 'codigo' 
    COLUNA_DISCIPLINA = 'disciplina' 
    
    MODELO_EMBEDDING = 'paraphrase-multilingual-MiniLM-L12-v2'

    # Validação e Carga
    if not ARQUIVO_DADOS_BRUTOS.exists():
        print(f"Erro: Arquivo de dados brutos não encontrado em: {ARQUIVO_DADOS_BRUTOS.resolve()}", file=sys.stderr)
    else:
        print(f"Carregando dados de: {ARQUIVO_DADOS_BRUTOS.resolve()}")
        df = pd.read_pickle(ARQUIVO_DADOS_BRUTOS)
        print(f"DataFrame original carregado com {len(df)} linhas.")
        
        colunas_necessarias = [COLUNA_CODIGO, COLUNA_DISCIPLINA] + COLUNAS_TEXTO
        if not all(col in df.columns for col in colunas_necessarias):
            print("\n--- ERRO DE CONFIGURAÇÃO ---", file=sys.stderr)
            print("O DataFrame não contém todas as colunas necessárias.", file=sys.stderr)
            print(f"Colunas necessárias: {colunas_necessarias}", file=sys.stderr)
            print(f"Colunas encontradas: {df.columns.tolist()}", file=sys.stderr)
        else:
            # Executar o pipeline que salva os dois artefatos
            processar_artefatos_disciplinas(
                df_original=df,
                colunas_texto=COLUNAS_TEXTO,
                coluna_codigo=COLUNA_CODIGO,
                coluna_disciplina=COLUNA_DISCIPLINA,
                nome_modelo=MODELO_EMBEDDING,
                path_saida_umap=ARQUIVO_SAIDA_UMAP,
                path_saida_grafo=ARQUIVO_SAIDA_GRAFO
            )