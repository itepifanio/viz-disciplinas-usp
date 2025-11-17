"""
Engloba todos os transformadores de dados.

Transforma os dados preprocessados:
1. Em embeddings
2. Em projeções UMAP
3. Em grafos k-NN
4. Em comunidades (Louvain)
"""

import pandas as pd
from typing import Optional

from transformer.embedding import DataEmbedder
from transformer.umap import UmapTransformer
from transformer.tsne import TsneTransformer
from transformer.graph import KNNGraphBuilder
from transformer.community import LouvainCommunityDetector # 1. IMPORTADO
from utils.config.model import TEXT_COL, MODEL_EMBEDDING
from utils.config.path import (
    umap_data_path,
    tsne_data_path,
    graph_data_path,
    community_data_path, # 1. IMPORTADO
    preprocessed_data_path,
    scrapper_data_path
)
from utils.data.reader import DataReader


class DataTransformerPipeline:
    def __init__(
        self,
        df: pd.DataFrame,
    ):
        """
        Args:
            df: Dataframe com preprocessamento mínimo (limpeza dos nan).
        """
        self._df = df
        self._umapper: Optional[UmapTransformer] = None
        self._grapher: Optional[KNNGraphBuilder] = None
        self._detector: Optional[LouvainCommunityDetector] = None # Adicionado
        
    def _execute(self) -> None:
        """
        Executa as transformações de dados em sequência:
        1. Gera embeddings.
        2. Prepara o UMAP.
        3. Prepara o Grafo k-NN.
        """
        to_embbed = self._df[TEXT_COL].fillna('').agg(' '.join, axis=1).tolist()
        
        embedder = DataEmbedder(model_name=MODEL_EMBEDDING, texts=to_embbed)
        embeddings = embedder.transform() 

        self._umapper = UmapTransformer(embeddings)
        self._tsner = TsneTransformer(embeddings)
        node_ids = self._df['codigo'].tolist()
        node_labels = self._df['disciplina'].fillna('Desconhecido').tolist()
        self._grapher = KNNGraphBuilder(
            embeddings,
            node_ids=node_ids,
            node_labels=node_labels,
        )

    def __call__(self) -> None:
        """
        Executa o pipeline de transformação de dados e salva os artefatos.
        """
        if (umap_data_path.exists() and 
            graph_data_path.exists() and
            tsne_data_path.exists() and 
            community_data_path.exists()):
            return

        self._execute()
        
        if self._umapper is None or self._grapher is None:
            raise RuntimeError("Pipeline não executado. Umapper ou Grapher estão Nulos.")

        # Etapa 1: Salvar UMAP
        self._umapper.to_file(
            umap_data_path,
            extra_cols={
                'codigo': self._df['codigo'],
                'disciplina': self._df['disciplina'],
                'commissao': self._df['commissao'],
            }
        )
        self._tsner.to_file(
            tsne_data_path,
            extra_cols={
                'codigo': self._df['codigo'],
                'disciplina': self._df['disciplina'],
                'commissao': self._df['commissao'],
            }
        )

        # Etapa 2: Salvar Grafo k-NN com Louvain aplicado
        self._detector = LouvainCommunityDetector(
            graph=self._grapher.graph, 
            random_state=42
        )
        self._detector.to_file(community_data_path)


if __name__ == "__main__":
    # Create the reader and obtain the preprocessed DataFrame via the
    reader = DataReader(
        scrapped_data_path=scrapper_data_path,
        output_dataframe_path=preprocessed_data_path
    )
    pipeline = DataTransformerPipeline(reader.dataframe)
    pipeline() # TODO: evitar executar todas as etapas se os arquivos já existirem
