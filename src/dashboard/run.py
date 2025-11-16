import os
import subprocess
from pathlib import Path


def check_data_exists():
    return Path('src/data/output.json').exists()

def run_scraper():
    print("Data not found. Running scraper...")
    original_dir = os.getcwd()
    try:
        os.chdir('src/scraper')
        subprocess.run(['scrapy', 'crawl', 'janus_disciplinas', '-o', '../data/output.json'], check=True)
    finally:
        os.chdir(original_dir)

def preprocess():
    print("Preprocessing data...")
    subprocess.run(['python', 'src/dashboard/pipeline.py'], check=True)

def start_streamlit():
    print("Starting Streamlit app...")
    subprocess.run(['streamlit', 'run', 'src/dashboard/app.py'], check=True)

def main():
    if not check_data_exists():
        run_scraper()

    preprocess()
    start_streamlit()

if __name__ == '__main__':
    main()
