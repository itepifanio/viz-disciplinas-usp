from typing import Self
from pathlib import Path

import networkx as nx


class DocenteDisciplinaGraphBuilder:
    def __init__(
        self, 
        node_ids: list[str], 
        node_labels: list[str], 
        docentes_data: list[str],
        separator: str = " | "
    ) -> None:
        """
        Constrói um grafo bipartido conectando Disciplinas aos seus Docentes Responsáveis.
        
        Args:
            node_ids: Lista de IDs das disciplinas (ex: códigos 'SME0123').
            node_labels: Lista de nomes das disciplinas.
            docentes_data: Lista de strings contendo os docentes (ex: "Nome A | Nome B").
            separator: O caractere separador usado na string de docentes. Default é " | ".
        """
        self._node_ids = node_ids
        self._node_labels = node_labels
        self._docentes_data = docentes_data
        self._separator = separator
        self._graph: nx.Graph | None = None

    @property
    def graph(self) -> nx.Graph:
        if self._graph is None:
            self.transform()

        return self._graph

    def transform(self) -> None:
        """
        Processa as listas e constrói o grafo NetworkX.
        
        Cria arestas entre o ID da disciplina e o nome de cada docente encontrado
        na string correspondente. Define o atributo 'bipartite' (0 para disciplina, 1 para docente).
        """
        if self._graph is None:
            self._graph = nx.Graph()

        # Itera sobre as disciplinas e a string de docentes correspondente
        for i, doc_str in enumerate(self._docentes_data):
            
            # Dados da Disciplina
            course_id = self._node_ids[i]
            course_label = self._node_labels[i]

            # 1. Adiciona o nó da Disciplina (Bipartite 0)
            # O check if exist é feito automaticamente pelo nx
            self._graph.add_node(
                course_id, 
                label=course_label, 
                type='disciplina', 
                bipartite=0
            )

            # Se não houver docentes (NaN ou string vazia), pula para o próximo
            if not doc_str or not isinstance(doc_str, str):
                continue

            # 2. Processa os Docentes
            lista_docentes = doc_str.split(self._separator)
            
            for docente in lista_docentes:
                docente_nome = docente.strip()
                
                if not docente_nome:
                    continue

                # Adiciona o nó do Docente (Bipartite 1)
                # Usamos o nome como ID do nó
                self._graph.add_node(
                    docente_nome, 
                    label=docente_nome, 
                    type='docente', 
                    bipartite=1
                )

                # 3. Cria a aresta (Disciplina <-> Docente)
                self._graph.add_edge(course_id, docente_nome)

    def to_file(self, path: Path) -> None:
        """
        Salva o grafo em um arquivo no formato GraphML.
        """        
        if path.exists():
            return

        nx.write_graphml(self.graph, path)
