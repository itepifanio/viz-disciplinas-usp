import pandas as pd
import networkx as nx
import community as community_louvain 
from typing import Dict, Optional, Any
from pathlib import Path

class LouvainCommunityDetector:
    """
    Carrega um grafo .graphml, detecta comunidades Louvain e salva
    o resultado (disciplina, codigo, comunidade) em um arquivo .pickle.
    """
    
    def __init__(self, 
                 graph_path: Path, 
                 random_state: int = 42):
        """
        Inicializa o detector de comunidades.

        Args:
            graph_path (Path): Caminho para o arquivo do grafo (.graphml).
            random_state (int): Seed para reprodutibilidade do algoritmo.
        """
        if not graph_path.exists():
            raise FileNotFoundError(f"Arquivo do grafo não encontrado em: {graph_path}")

        try:
            self._graph = nx.read_graphml(graph_path)
        except Exception as e:
            raise IOError(f"Falha ao ler o arquivo do grafo em {graph_path}. Erro: {e}")

        if self._graph is None:
            raise ValueError(f"O grafo carregado de {graph_path} é Nulo.")
        
        self._random_state = random_state
        self._partition: Optional[Dict[Any, int]] = None

    def _detect_communities(self) -> None:
        """Método interno para executar o algoritmo Louvain."""
        self._partition = community_louvain.best_partition(
            self._graph, 
            random_state=self._random_state
        )

    @property
    def partition(self) -> Dict[Any, int]:
        """
        Retorna a partição de comunidade (dicionário {node: community_id}).

        Executa a detecção na primeira vez que esta property é acessada.
        """
        if self._partition is None:
            self._detect_communities()
        
        if self._partition is None:
            # Isso só aconteceria se _detect_communities falhasse em atribuir
            raise RuntimeError("Falha na detecção. A partição ainda é Nula.")
            
        return self._partition

    def to_file(self, path: Path) -> None:
        """
        Gera o DataFrame de comunidades e o salva em um arquivo pickle.

        O DataFrame conterá as colunas: 'disciplina', 'codigo', 'comunidade'.
        
        Args:
            path (Path): O caminho do arquivo .pickle de saída.
        """
        if path.exists():
            return # Sai silenciosamente se o arquivo já existe
        
        # 1. Garante que as comunidades foram detectadas
        partition_map = self.partition
        
        # 2. Prepara os dados para o DataFrame
        data_list = []
        for node_id, attrs in self._graph.nodes(data=True):
            data_list.append({
                'codigo': node_id,
                'disciplina': attrs.get('label', None),
                'comunidade': partition_map.get(node_id, None)
            })
            
        if not data_list:
            # Se não houver dados, não cria o arquivo
            return

        # 3. Cria o DataFrame
        df_out = pd.DataFrame(data_list)
        
        # 4. Converte a coluna de comunidade para o tipo 'category'
        try:
            df_out['comunidade'] = df_out['comunidade'].astype('Int64').astype('category')
        except Exception:
            df_out['comunidade'] = df_out['comunidade'].astype('category')

        # 5. Salva em pickle
        path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_pickle(path)