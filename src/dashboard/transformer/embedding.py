"""
Transforma textos em embeddings.
"""

import numpy as np
import nltk
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
import re

class DataEmbedder:
    def __init__(
        self, 
        model_name: str,
        texts: list[str] | None = None
    ) -> None:
        """
        Inicializa o DataEmbedder com o nome do modelo de embedding.

        Configura as stopwords em português e inglês e uma fez chamado, 
        carrega o modelo de embeddings e retorna os array de embeddings 
        para os textos fornecidos.        
        """
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            print("Baixando stopwords (pt e en) do NLTK...")
            nltk.download('stopwords')
            
        stop_words_pt = set(stopwords.words('portuguese'))
        stop_words_en = set(stopwords.words('english'))
        self._stop_words: set[str] = stop_words_pt.union(stop_words_en)
        self._texts = texts
        self._model_name = model_name

    def transform(self) -> np.ndarray:
        model = SentenceTransformer(self._model_name)
        return model.encode(
            [
                self._filter_stopwords(text, self._stop_words)
                for text in self._texts
            ], 
            show_progress_bar=True
        )

    def _filter_stopwords(self, text: str, stop_words: set[str]) -> str:
        """
        Remove stopwords de um texto.
        """
        if not isinstance(text, str):
            return "" 
        
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text) 
        
        palavras = [
            palavra for palavra in text.split() 
            if palavra not in stop_words and len(palavra) > 2
        ]

        return ' '.join(palavras)
