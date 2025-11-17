"""
Engloba todos os transformadores de dados.

Transforma os dados preprocessados:
1. Em embeddings
2. Em projeções UMAP
3. Em grafos k-NN
"""

import pandas as pd

from transformer.embedding import DataEmbedder
from transformer.umap import UmapTransformer
from transformer.tsne import TsneTransformer
from transformer.graph import KNNGraphBuilder
from utils.config.model import TEXT_COL, MODEL_EMBEDDING
from utils.config.path import (
    umap_data_path,
    tsne_data_path,
    graph_data_path,
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
            embedder: Gerador de embeddings a partir de uma lista de textos.
            umapper: Aplicador de UMAP nos embeddings.
            grapher: Gerador de grafo k-NN a partir dos embeddings
        """
        self._df = df
        
    def _execute(self) -> None:
        """
        Executa as transformações de dados em sequência:
        1. Gera embeddings.
        2. Aplica UMAP.
        3. Constrói grafo k-NN.
        """
        to_embbed = self._df[TEXT_COL].fillna('').agg(' '.join, axis=1).tolist()
        
        embedder = DataEmbedder(model_name=MODEL_EMBEDDING, texts=to_embbed)
        embeddings = embedder.transform() # TODO: improve this API

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
        Executa o pipeline de transformação de dados.
        """
        if umap_data_path.exists() and graph_data_path.exists() and tsne_data_path.exists():
            return

        self._execute()
        self._umapper.to_file(
            umap_data_path,
            extra_cols={ # TODO: avoid hardcoding
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
        self._grapher.to_file(graph_data_path)

if __name__ == "__main__":
    # Create the reader and obtain the preprocessed DataFrame via the
    reader = DataReader(
        scrapped_data_path=scrapper_data_path,
        output_dataframe_path=preprocessed_data_path
    )
    pipeline = DataTransformerPipeline(reader.dataframe)
    pipeline() # TODO: evitar executar todas as etapas se os arquivos já existirem
