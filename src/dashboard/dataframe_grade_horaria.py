import pandas as pd
import networkx as nx
from pathlib import Path
from networkx import Graph
from utils.config.subjects import obrigatorias

# TODO: refatorar para seguir a API lazy loading com .to_file()
class DashboardArtifactGenerator:
    def __init__(
        self,
        df_raw: pd.DataFrame,
        df_comm: pd.DataFrame,
        knn_graph: Graph,
        output_dir: Path
    ):
        """
        Classe responsável por gerar os arquivos finais consumidos pelo Dashboard.
        
        Args:
            df_raw: DataFrame principal com os dados do scrap pré-processados.
            df_comm: DataFrame com as informações de comunidade extraídas via Louvain.
            knn_graph: Grafo k-NN original das disciplinas.
            output_dir: Diretório onde os artefatos serão salvos.
        """
        self._df_raw = df_raw
        self._df_comm = df_comm
        self._knn_graph = knn_graph
        self.output_dir = output_dir

        # Configuração hardcoded dos filtros
        self.institutos_alvo = [
            "Instituto de Ciências Matemáticas e de Computação",
            "Instituto de Matemática, Estatística e Ciência da Computação",
            "Instituto de Matemática e Estatística"
        ]

    def run(self):
        """
        Executa o pipeline sequencial:
        1. Gera Tabela Mestre.
        2. Gera Grafo Docentes.
        3. Gera Grafo Disciplinas.
        """
        print("--- [DashboardGenerator] Iniciando geração de artefatos ---")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Gerar DataFrame Unificado
        df_final = self._gerar_dataset_dashboard()
        
        path_df = self.output_dir / "dados_dashboard_completo.pickle"
        df_final.to_pickle(path_df)
        print(f"✅ [1/3] Dataset salvo em: {path_df}")

        # 2. Gerar Grafo Docentes
        G_doc = self._construir_grafo_docentes(df_final)
        
        path_doc = self.output_dir / "grafo_docentes_enrichido.graphml"
        nx.write_graphml(G_doc, path_doc)
        print(f"✅ [2/3] Grafo Docentes salvo em: {path_doc}")

        # 3. Gerar Grafo Disciplinas
        G_disc = self._enriquecer_grafo_disciplinas(df_final)
        
        path_disc = self.output_dir / "grafo_disciplinas_enrichido.graphml"
        nx.write_graphml(G_disc, path_disc)
        print(f"✅ [3/3] Grafo Disciplinas salvo em: {path_disc}")

    def _gerar_dataset_dashboard(self) -> pd.DataFrame:
        """Gera o dataset unificado tratando colisões de nomes."""
        df_main = self._df_raw.copy()
        df_comm = self._df_comm.copy()

        df_main['codigo'] = df_main['codigo'].astype(str).str.strip()
        
        if 'codigo' not in df_comm.columns and df_comm.index.name == 'codigo':
            df_comm = df_comm.reset_index()
        df_comm['codigo'] = df_comm['codigo'].astype(str).str.strip()

        # --- CORREÇÃO DO ERRO AQUI ---
        # Se o df de comunidade tiver 'disciplina', removemos antes do merge
        # para evitar a criação de 'disciplina_x' e 'disciplina_y'
        if 'disciplina' in df_comm.columns:
            df_comm = df_comm.drop(columns=['disciplina'])

        # Merge (agora seguro)
        df_merged = pd.merge(df_main, df_comm, on='codigo', how='left')

        # Identificar Obrigatórias
        df_merged['eh_obrigatoria'] = df_merged['codigo'].isin(obrigatorias)

        # Filtrar Instituto
        # Verifica qual coluna de comissão existe
        col_comissao = 'commissao' if 'commissao' in df_merged.columns else 'comissao'
        
        if col_comissao not in df_merged.columns:
            # Fallback se não achar a coluna, para não quebrar, cria vazia
            print(f"Aviso: Coluna '{col_comissao}' não encontrada. Criando vazia.")
            df_merged[col_comissao] = 'Desconhecido'

        df_final = df_merged[df_merged[col_comissao].isin(self.institutos_alvo)].copy()
        
        print(f"Total de disciplinas filtradas: {len(df_final)}")
        return df_final

    def _construir_grafo_docentes(self, df: pd.DataFrame) -> nx.Graph:
        """Constrói o grafo bipartido Docente-Disciplina"""
        G = nx.Graph()
        for _, row in df.iterrows():
            node_id = str(row['codigo']).strip()
            
            # Adiciona segurança ao acessar colunas
            disciplina_nome = row['disciplina'] if 'disciplina' in row else f"Disciplina {node_id}"
            comissao_nome = str(row.get('commissao', row.get('comissao', '')))

            # Nó Disciplina
            G.add_node(
                node_id, 
                label=disciplina_nome, 
                bipartite=0, 
                type='disciplina',
                comunidade=int(row['comunidade']) if pd.notna(row.get('comunidade')) else -1,
                is_mandatory=bool(row['eh_obrigatoria']),
                institute=comissao_nome
            )

            # Nós Docentes
            raw_doc = row.get('docentes_responsaveis')
            if pd.notna(raw_doc) and str(raw_doc).strip():
                doc_list = [d.strip() for d in str(raw_doc).split('|') if d.strip()]
                for doc_name in doc_list:
                    G.add_node(doc_name, label=doc_name, bipartite=1, type='docente')
                    G.add_edge(node_id, doc_name)
        return G

    def _enriquecer_grafo_disciplinas(self, df: pd.DataFrame) -> nx.Graph:
        """Enriquece o grafo k-NN existente"""            
        G = self._knn_graph.copy()

        # Filtra nós
        codigos_validos = set(df['codigo'])
        nos_remover = [n for n in G.nodes() if str(n).strip() not in codigos_validos]
        G.remove_nodes_from(nos_remover)

        # Adiciona Metadados
        df_indexed = df.set_index('codigo')
        for node in G.nodes():
            nid = str(node).strip()
            if nid in df_indexed.index:
                row = df_indexed.loc[nid]
                
                disciplina_nome = row['disciplina'] if 'disciplina' in row else f"Disciplina {nid}"
                comissao_nome = str(row.get('commissao', row.get('comissao', '')))

                G.nodes[node].update({
                    'label': str(disciplina_nome),
                    'comunidade': int(row['comunidade']) if pd.notna(row.get('comunidade')) else -1,
                    'is_mandatory': bool(row['eh_obrigatoria']),
                    'institute': comissao_nome,
                    'type': 'disciplina'
                })

        return G
