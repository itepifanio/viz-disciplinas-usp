"""
Conecta embeddings de nós para construir um grafo k-NN usando NetworkX.
"""

from typing import Self
from pathlib import Path

import numpy as np

import networkx as nx
from sklearn.neighbors import NearestNeighbors


class KNNGraphBuilder:
    def __init__(
        self, 
        embeddings: np.ndarray,
        node_ids: list[str], 
        node_labels: list[str], 
        k: int = 5
    ) -> None:
        """
        Utiliza algoritmos não-supervisionados para construir um grafo k-NN a partir de embeddings.
        
        Args:
            embeddings: Matriz de embeddings dos nós.
            node_ids: Lista de IDs únicos para cada nó, e.g, códigos de disciplinas.
            node_labels: Lista de labels (nomes) para cada nó, e.g, nomes de disciplinas.
            path: Path para salvar o grafo gerado.
            k: Número de vizinhos mais próximos para conectar no grafo.
        """
        self._embeddings = embeddings
        self._node_ids = node_ids
        self._node_labels = node_labels
        self._k = k
        self._graph: nx.Graph | None = None

    @property
    def graph(self) -> nx.Graph:
        if self._graph is None:
            self.transform()

        return self._graph

    def transform(self) -> None:
        """
        Constrói um grafo NetworkX conectando os k-vizinhos mais próximos.
        
        Utiliza o algoritmo de NearestNeighbors do scikit-learn para encontrar os vizinhos
        mais próximos com base nos embeddings fornecidos.
        """
        if self._graph is None:
            self._graph = nx.Graph()

        nn = NearestNeighbors(
            n_neighbors=self._k + 1,  # k+1 pois o primeiro é o próprio ponto
            metric='cosine', 
            algorithm='brute'
        )
        nn.fit(self._embeddings)
        
        # Obtemos os índices dos vizinhos para cada ponto
        # Não precisamos das distâncias, apenas dos índices
        indices = nn.kneighbors(self._embeddings, return_distance=False)

        # Adiciona todos os nós e seus metadados
        for i, node_id in enumerate(self._node_ids):
            self._graph.add_node(node_id, label=self._node_labels[i])

        for i, neighbors in enumerate(indices):
            origem_id = self._node_ids[i]
            
            # Iteramos de 1 a k (pulamos o 0, que é o self-loop)
            for j in range(1, self._k + 1): 
                vizinho_idx = neighbors[j]
                vizinho_id = self._node_ids[vizinho_idx]
                
                # Adicionamos a aresta (o Grafo lida com duplicatas)
                self._graph.add_edge(origem_id, vizinho_id)

    def to_file(self, path: Path) -> None:
        """
        Salva o grafo em um arquivo no formato GraphML.
        """
        if path.exists():
            return

        nx.write_graphml(self.graph, path)
