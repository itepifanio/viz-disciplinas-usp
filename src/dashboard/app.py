"""
Streamlit page entrypoint.
"""

import streamlit as st

disciplinas_page = st.Page("disciplinas.py", title="Disciplinas", icon="📖")
hierarquia_page = st.Page("hierarchy.py", title="Hierarquia", icon="🌳")
embeddings_page = st.Page("embeddings.py", title="Embeddings", icon="🕸️")
grade_curricular_page = st.Page("grade_curricular.py", title="Grade Curricular", icon="🏫")

pg = st.navigation([disciplinas_page, hierarquia_page, embeddings_page, grade_curricular_page])

pg.run()
