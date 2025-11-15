from viz.treemap import treemap

from utils import get_data

import streamlit as st

st.plotly_chart(treemap(get_data()))
