# %%
# CÉLULA 1: Importações e Definição da Função

import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer

def gerar_embeddings_para_dataframe(df: pd.DataFrame, coluna_texto: str, nome_modelo: str = 'paraphrase-multilingual-MiniLM-L12-v2') -> pd.DataFrame:
    """
    Gera embeddings para uma coluna de texto em um DataFrame e os adiciona como uma nova coluna.

    Args:
        df (pd.DataFrame): O DataFrame de entrada.
        coluna_texto (str): O nome da coluna que contém os textos a serem processados.
        nome_modelo (str): O nome do modelo Sentence Transformer a ser usado.

    Returns:
        pd.DataFrame: O DataFrame original com uma nova coluna contendo os embeddings.
    """
    print(f"Carregando o modelo '{nome_modelo}'... Isso pode levar um momento.")
    try:
        model = SentenceTransformer(nome_modelo)
    except Exception as e:
        print(f"Erro ao carregar o modelo: {e}")
        print("Verifique sua conexão com a internet ou o nome do modelo.")
        return df

    print("Gerando embeddings... Por favor, aguarde.")
    
    # 1. Garante que a coluna de texto não tenha valores nulos (NaN)
    textos = df[coluna_texto].fillna('').tolist()

    # 2. Gera os embeddings para todos os textos de uma vez (processamento em lote)
    embeddings = model.encode(textos, show_progress_bar=True)

    # 3. Adiciona os embeddings como uma nova coluna
    nova_coluna = f'{coluna_texto}_embedding'
    df[nova_coluna] = list(embeddings)
    
    print(f"Embeddings gerados e adicionados na coluna '{nova_coluna}'.")
    return df


# %%
# CÉLULA 2: Execução do Código

# Bloco principal para garantir que o código só rode quando o script for executado
if __name__ == "__main__":
    # project_dir agora é '...\src\dashboard\prep'
    project_dir = Path.cwd() 
    
    # CORREÇÃO AQUI:
    # A partir de 'prep', subimos um nível ('..') para 'dashboard'
    # e então entramos em 'files'.
    file_path = project_dir / '..' / 'files' / 'output.csv' 
    
    print(f"Carregando dados de: {file_path}")
    try:
        df_disciplinas = pd.read_csv(file_path)

        # Chama a função para gerar os embeddings para a coluna 'objetivos'
        df_com_embeddings = gerar_embeddings_para_dataframe(df_disciplinas, coluna_texto='objetivos')

        # Exibe o resultado
        print("\n--- Resultado Final ---")
        print(df_com_embeddings.head())

        # Opcional: verificar o conteúdo de um embedding
        if 'objetivos_embedding' in df_com_embeddings.columns:
            print("\nExemplo do primeiro embedding (primeiros 5 valores):")
            print(df_com_embeddings['objetivos_embedding'].iloc[0][:5])

    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado em '{file_path}'.")
        print(f"Verifique se o caminho e a estrutura de pastas estão corretos.")
        print(f"Diretório atual: {project_dir}")