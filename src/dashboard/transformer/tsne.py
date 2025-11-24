"""
Projeta os embeddings usando t-SNE para visualização de dados.
"""

from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.manifold import TSNE


class TsneTransformer:
    def __init__(
        self,
        embeddings: np.ndarray,
        perplexity: float = 30.0,
        n_components: int = 2,
        metric: str = 'cosine',
        random_state: int = 42,
        n_iter: int = 1000,
    ) -> None:
        self._embeddings = embeddings
        self._perplexity = perplexity
        self._n_components = n_components
        self._metric = metric
        self._random_state = random_state
        self._n_iter = n_iter
        self._model_embeddings: np.ndarray | None = None

    @property
    def model_embeddings(self) -> np.ndarray:
        if self._model_embeddings is None:
            self.transform()

        return self._model_embeddings

    def transform(self) -> None:
        tsne = TSNE(
            n_components=self._n_components,
            perplexity=self._perplexity,
            metric=self._metric,
            random_state=self._random_state,
            max_iter=self._n_iter,
            init='pca'
        )
        self._model_embeddings = tsne.fit_transform(self._embeddings)

    def to_file(self, path: Path, extra_cols: dict) -> None:
        """
        Salva as projeções t-SNE em um arquivo pickle contendo um DataFrame.
        """
        if path.exists():
            return

        embedding_2d = self.model_embeddings
        df_tsne = pd.DataFrame({
            **extra_cols,
            'tsne_x': embedding_2d[:, 0],
            'tsne_y': embedding_2d[:, 1]
        })

        df_tsne.to_pickle(path)
