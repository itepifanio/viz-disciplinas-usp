#!/bin/bash

if [ ! -f "nbs/output.json" ]; then
    echo "Data not found. Running scraper..."
    cd src/scraper
    scrapy crawl janus_disciplinas -o ../../nbs/output.json
    cd ../..
fi

echo "Starting Streamlit app..."
streamlit run src/dashboard/app.py
