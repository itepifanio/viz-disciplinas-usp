"""
Utility module for model configuration.
"""

# Modelo de embedding a ser utilizado na geração dos embeddings de texto
MODEL_EMBEDDING = 'paraphrase-multilingual-MiniLM-L12-v2'

# Colunas de texto a serem consideradas para geração dos embeddings
TEXT_COL = ['objetivos', 'justificativa', 'conteudo']
