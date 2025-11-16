"""
Projeta os UMAP para visualização de dados.
"""

from typing import Self
from pathlib import Path

import numpy as np
import pandas as pd

import umap

class UmapTransformer:
    def __init__(
        self, 
        embeddings: np.ndarray,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        n_components: int = 2,
        metric: str = 'cosine',
        random_state: int = 42
    ) -> None:
        self._embeddings = embeddings
        self._n_neighbors = n_neighbors
        self._min_dist = min_dist
        self._n_components = n_components
        self._metric = metric
        self._random_state = random_state
        self._model_embeddings: np.ndarray | None = None
        
    @property
    def model_embeddings(self) -> np.ndarray:
        if self._model_embeddings is None:
            self.transform()

        return self._model_embeddings

    def transform(self) -> None:
        reducer = umap.UMAP(
            n_neighbors=self._n_neighbors, 
            min_dist=self._min_dist, 
            n_components=self._n_components, 
            metric=self._metric, 
            random_state=self._random_state
        )
        self._model_embeddings = reducer.fit_transform(self._embeddings)

    def to_file(self, path: Path, extra_cols: dict) -> None:
        """
        Salva o modelo UMAP treinado em um arquivo pickle.
        
        O arquivo pickle carrega um dataframe.
        """
        if path.exists():
            return
        
        embedding_2d = self.model_embeddings
        df_umap = pd.DataFrame({
            **extra_cols,
            'umap_x': embedding_2d[:, 0],
            'umap_y': embedding_2d[:, 1]
        })
        
        # Salvar Artefato 1
        df_umap.to_pickle(path)
