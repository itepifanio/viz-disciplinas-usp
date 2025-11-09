"""
Streamlit page entrypoint.
"""

import streamlit as st

main_page = st.Page("main.py", title="Main Page", icon="🎈")
disciplinas_page = st.Page("disciplinas.py", title="Disciplinas", icon="❄️")
embeddings_page = st.Page("embeddings.py", title="Embeddings", icon="🎉")

pg = st.navigation([main_page, disciplinas_page, embeddings_page])

pg.run()
