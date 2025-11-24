import pandas as pd
from typing import Optional
from transformer.embedding import DataEmbedder
from transformer.umap import UmapTransformer
from transformer.tsne import TsneTransformer
from transformer.graph import KNNGraphBuilder
from transformer.responsaveis import DocenteDisciplinaGraphBuilder 
from transformer.community import LouvainCommunityDetector
from dataframe_grade_horaria import DashboardArtifactGenerator 
from utils.config.model import TEXT_COL, MODEL_EMBEDDING
from utils.config.path import (
    umap_data_path,
    tsne_data_path,
    preprocessed_data_path,
    scrapper_data_path,
    BASE_DIR,
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
        self._bipartite_grapher: Optional[DocenteDisciplinaGraphBuilder] = None 
        self._detector: Optional[LouvainCommunityDetector] = None
        self._dashboard_gen: Optional[DashboardArtifactGenerator] = None

    def _execute(self) -> None:
        """
        Executa as transformações de dados em sequência:
        1. Gera embeddings.
        2. Prepara o UMAP e t-SNE.
        3. Prepara o Grafo Bipartido (Docentes).
        """
        # --- Preparação de Texto e IDs ---
        to_embbed = self._df[TEXT_COL].fillna('').agg(' '.join, axis=1).tolist()
        node_ids = self._df['codigo'].tolist()
        node_labels = self._df['disciplina'].fillna('Desconhecido').tolist()
        
        # --- 1. Embeddings ---
        embedder = DataEmbedder(model_name=MODEL_EMBEDDING, texts=to_embbed)
        embeddings = embedder.transform() 

        # --- 2. UMAP and t-SNE ---
        self._umapper = UmapTransformer(embeddings)
        self._tsner = TsneTransformer(embeddings)
        node_ids = self._df['codigo'].tolist()
        node_labels = self._df['disciplina'].fillna('Desconhecido').tolist()
        
        # --- 3. Grafo Bipartido ---
        self._grapher = KNNGraphBuilder(
            embeddings,
            node_ids=node_ids,
            node_labels=node_labels,
        )
        docentes_data = self._df['docentes_responsaveis'].fillna('').astype(str).tolist()
        self._bipartite_grapher = DocenteDisciplinaGraphBuilder(
            node_ids=node_ids,
            node_labels=node_labels,
            docentes_data=docentes_data
        )

        # -- 4. Louvain community ---
        self._detector = LouvainCommunityDetector(
            graph=self._grapher.graph, 
            random_state=42
        )

        # --- 4. Grafo Bipartido (Novo) ---
        # Tratamento para garantir que seja string e lidar com NaNs
        docentes_data = self._df['docentes_responsaveis'].fillna('').astype(str).tolist()
        
        self._bipartite_grapher = DocenteDisciplinaGraphBuilder(
            node_ids=node_ids,
            node_labels=node_labels,
            docentes_data=docentes_data
        )

    def __call__(self) -> None:
        """
        Executa o pipeline de transformação de dados e salva os artefatos.
        """
        if (umap_data_path.exists() and
            tsne_data_path.exists()): # TODO: adicionar artefatos do dashboard
            # Se os arquivos já existem, não precisa reprocessar tudo
            return

        self._execute()

        if (self._umapper is None or 
            self._grapher is None or 
            self._bipartite_grapher is None):
            raise RuntimeError("Pipeline incompleto. Transformadores estão Nulos.")

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

        # TODO: adaptar API do DashboardArtifactGenerator
        DashboardArtifactGenerator(
            df_raw=self._df,
            df_comm=self._detector.dataframe,
            knn_graph=self._grapher.graph,
            output_dir=BASE_DIR / 'grade_horaria'
        ).run()

        # Etapa 3: Salvar Grafo Bipartido (Novo)
        self._bipartite_grapher.to_file(bipartite_graph_data_path)
        
        # Etapa 4: Detecção de Comunidades
        # Esta etapa depende que 'graph_data_path' tenha sido salvo (k-NN).
        self._detector = LouvainCommunityDetector(
            graph_path=graph_data_path, 
            random_state=42
        )
        self._detector.to_file(community_data_path)

        # 3. ADICIONADO (CASO 2): Roda o dashboard ao final do processo
        self._run_dashboard_gen()

    def _run_dashboard_gen(self):
        """Helper simples para instanciar e rodar o gerador"""
        # Define output dir fixo como subpasta 'grade_horaria'
        out_dir = preprocessed_data_path.parent / 'grade_horaria'
        
        self._dashboard_gen = DashboardArtifactGenerator(
            raw_data_path=preprocessed_data_path,
            community_path=community_data_path,
            original_knn_graph_path=graph_data_path,
            output_dir=out_dir
        )
        self._dashboard_gen.run()


if __name__ == "__main__":
    reader = DataReader(
        scrapped_data_path=scrapper_data_path,
        output_dataframe_path=preprocessed_data_path
    )
    pipeline = DataTransformerPipeline(reader.dataframe)
    pipeline() # TODO: evitar executar todas as etapas se os arquivos já existirem
