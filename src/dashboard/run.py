import os
import subprocess
from pathlib import Path

def check_data_exists():
    return Path('nbs/output.json').exists()

def run_scraper():
    print("Data not found. Running scraper...")
    original_dir = os.getcwd()
    try:
        os.chdir('src/scraper')
        subprocess.run(['scrapy', 'crawl', 'janus_disciplinas', '-o', '../../nbs/output.json'], check=True)
    finally:
        os.chdir(original_dir)

def start_streamlit():
    print("Starting Streamlit app...")
    subprocess.run(['streamlit', 'run', 'src/dashboard/app.py'], check=True)

# TODO: 
# 1. adicionar a geração dos dados de embeddings aqui
# 2. mover os arquivos para a pasta src/data/*

def main():
    if not check_data_exists():
        run_scraper()
    start_streamlit()

if __name__ == '__main__':
    main()
