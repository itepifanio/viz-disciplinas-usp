"""
Utility module for configuration paths.
"""

from pathlib import Path

BASE_DIR = Path("src/data")

# path with scrapped data
scrapper_data_path = BASE_DIR / "output.json"

# path to store the preprocessed dataframe with correct typing and nan handling
preprocessed_data_path = BASE_DIR / "output.pickle"

# umap pickled data path
umap_data_path = BASE_DIR / "umap.pickle"

# graph html data path
graph_data_path = BASE_DIR / "graph.graphml"
